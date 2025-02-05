import asyncio
from datetime import datetime, timezone, timedelta
from typing import Optional

import async_timeout
import discord
from discord.ext import tasks

from app.models.database import get_db
from app.models.models import InteractionType, Interaction
from app.services.database_service import DatabaseService
from app.services.pynostr_sync import NostrSync
from config.config import Config
from utils.logger import Logger
import pytz


class DiscordCollector(discord.Client):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db_service = DatabaseService()
        self.logger = Logger('discord_collector')
        self.batch_size = 100
        self.batch_timeout = 10  # 秒
        self.message_queue = None
        self.nostr_sync = NostrSync(Config.NOSTR_RELAY_URLS, Config.NOSTR_PRIVATE_KEY)

    async def setup_hook(self) -> None:
        """这个方法会在客户端初始化时被调用，在正确的事件循环中设置"""
        self.message_queue = asyncio.Queue()
        self.loop.create_task(self.process_message_queue())
        self.collect_messages.start()

    async def on_ready(self):
        """当 Discord 客户端准备就绪时触发"""
        self.logger.info(f'Discord collector started successfully, Logged in as {self.user}')

    async def process_message_queue(self):
        """处理消息队列"""
        while True:
            batch = []
            try:
                # 尝试在超时时间内收集足够的消息
                async with async_timeout.timeout(self.batch_timeout):
                    while len(batch) < self.batch_size:
                        message = await self.message_queue.get()
                        batch.append(message)
                        if len(batch) >= self.batch_size:
                            # 达到批处理大小，立即处理
                            await self.save_messages_batch(batch)
                            batch = []  # 清空批次
            except asyncio.TimeoutError:
                if batch:
                    await self.save_messages_batch(batch)
            except Exception as e:
                self.logger.error(f"Error processing message batch: {str(e)}")
                await asyncio.sleep(1)

    async def save_messages_batch(self, batch: list[discord.Message]):
        """批量保存消息"""
        db = next(get_db())
        try:
            # 准备批量数据
            interactions_data = []
            for message in batch:
                interaction_data = {
                    'message_id': str(message.id),
                    'channel_id': str(message.channel.id),
                    'user_id': str(message.author.id),
                    'username': message.author.name,
                    'interaction_content': message.content,
                    'interaction_time': message.created_at,
                    'note': '',
                    'type': InteractionType.MESSAGE.value,
                    'post_time': message.created_at
                }
                interactions_data.append(interaction_data)

                # 判断消息是否为回复
                if message.reference and message.reference.message_id:
                    info = {
                        'message_id': message.reference.message_id,
                        'channel_id': message.reference.channel_id
                    }
                    interaction_data['note'] = str(info)
                    interaction_data[
                        'type'] = InteractionType.REPLY.value if message.reference.channel_id == message.channel.id else InteractionType.RETWEET.value

                # # 判断消息是否存在过表情互动
                # if message.reactions:
                #     for reaction in message.reactions:
                #         for user in await reaction.users().flatten():
                #             info = {
                #                 'emoji': reaction.emoji,
                #                 'user': user.name,
                #                 'message_id': message.id,
                #                 'channel_id': message.channel.id
                #             }
                #             interactions_data.append({
                #                 **interaction_data,
                #                 'note': str(info),
                #                 'type': InteractionType.LIKE.value
                #             })

            # 批量保存到数据库
            if interactions_data:
                saved_count = self.db_service.save_interactions_batch(db, interactions_data)
                self.logger.info(f"Saved {saved_count} messages successfully")

        except Exception as e:
            self.logger.error(f"Error saving message batch: {str(e)}")
        finally:
            db.close()

    @tasks.loop(seconds=10)
    async def collect_messages(self):
        """定时收集消息的任务"""
        db = next(get_db())
        try:
            self.logger.info("Starting message collection task")
            channels = self.db_service.get_active_channels(db)

            for channel in channels:
                channel_id = int(channel.channel_id)
                discord_channel = self.get_channel(channel_id)

                if discord_channel:
                    frequency = channel.update_frequency
                    if self.check_channel_collect_time(channel_id, frequency):
                        collect_start_time = channel.collect_start_time
                        collect_end_time = channel.collect_end_time
                        last_message_post_time = None

                        # 确保时间有正确的时区信息
                        if collect_start_time:
                            collect_start_time = collect_start_time if collect_start_time.tzinfo else collect_start_time.replace(
                                tzinfo=timezone.utc)
                        if collect_end_time:
                            collect_end_time = collect_end_time if collect_end_time.tzinfo else collect_end_time.replace(
                                tzinfo=timezone.utc)

                        # 使用上次记录的最后消息时间
                        last_message_id = self.db_service.select_max_interaction_id(db, channel_id)
                        if last_message_id:
                            # 获取这条消息的实际时间并加1毫秒
                            last_message_post_time = await self.get_message_created_time(
                                discord_channel,
                                last_message_id
                            )
                        if last_message_post_time:
                            last_message_post_time = last_message_post_time if last_message_post_time.tzinfo else last_message_post_time.replace(
                                tzinfo=timezone.utc)

                        if collect_start_time and last_message_post_time:
                            collect_start_time = max(collect_start_time, last_message_post_time)
                        elif last_message_post_time:
                            collect_start_time = last_message_post_time
                        elif collect_start_time:
                            collect_start_time = collect_start_time
                        else:
                            collect_start_time = None

                        # 保存采集日志
                        self.db_service.save_channel_collect_log(db, channel_id, collect_start_time, collect_end_time)

                        self.logger.info(f"正在收集频道 {discord_channel.name}:{channel_id} 的消息 "
                                         f"开始时间: {collect_start_time}, 结束时间: {collect_end_time}")

                        history_messages = discord_channel.history(
                            after=collect_start_time,
                            before=collect_end_time,
                            oldest_first=True  # 确保按时间顺序处理消息
                        )
                        message_count = 0
                        async for message in history_messages:
                            # 只处理文字消息
                            message_count += 1
                            # if message.content and message.type == MessageType.default:
                            if message.content or message.reference:
                                await self.message_queue.put(message)
                            else:
                                print(message)
                        self.logger.info(
                            f"Collected {message_count} messages for channel {discord_channel.name}:{channel_id}")
                else:
                    self.logger.warning(f"Channel {channel.channel_id} not found")

        except Exception as e:
            self.logger.error(f"Error in collect_messages task: {str(e)}")
        finally:
            db.close()

    def check_channel_collect_time(self, channel_id, frequency) -> bool:
        if frequency is None:
            return False

        db = next(get_db())
        # 解析频率
        try:
            # 从未采集过
            last_collect_time = self.db_service.get_channel_last_collect_time(db, channel_id)
            if last_collect_time is None:
                return True

            # 确保 last_collect_time 有时区信息
            if last_collect_time.tzinfo is None:
                last_collect_time = last_collect_time.replace(tzinfo=pytz.UTC)

            amount = int(''.join(filter(str.isdigit, frequency)))
            unit = ''.join(filter(str.isalpha, frequency)).lower()

            # 转换为秒数
            seconds_map = {
                's': 1,
                'm': 60,
                'h': 3600,
                'd': 86400
            }

            if unit not in seconds_map:
                self.logger.error(f"Invalid frequency unit: {unit}")
                return False

            interval_seconds = amount * seconds_map[unit]

            # 计算下次允许采集的时间
            next_collect_time = last_collect_time + timedelta(seconds=interval_seconds)
            current_time = datetime.now(pytz.UTC)

            self.logger.debug(f"当前时间: {current_time}, 下次采集时间: {next_collect_time}")
            return current_time >= next_collect_time

        except Exception as e:
            self.logger.error(f"Error parsing frequency '{frequency}': {str(e)}")
            return False
        finally:
            db.close()

    @tasks.loop(hours=24)
    async def nostr_publish(self):
        """定时发布消息到 Nostr"""
        db = next(get_db())
        try:
            self.logger.info("Starting Nostr publish task")
            unsynced_interactions = self.db_service.get_unsynced_interactions(db)
            total, interactions = unsynced_interactions
            self.logger.info(f"Found {total} unsynced interactions")

            self.nostr_sync.sync_interactions(interactions)
        except Exception as e:
            self.logger.error(f"Error in nostr_publish task: {str(e)}")
        finally:
            db.close()

    async def on_raw_reaction_add(self, payload):
        """
        处理添加反应(点赞)事件
        payload 包含:
            - message_id: 消息ID
            - channel_id: 频道ID
            - user_id: 用户ID
            - emoji: 表情符号
        """
        try:
            db = next(get_db())
            try:
                channel_id = payload.channel_id
                # 判断channel_id是否在
                channel = self.db_service.get_channel(db, channel_id)
                if channel:
                    channel = await self.fetch_channel(channel_id)
                    message = await channel.fetch_message(payload.message_id)
                    user = await self.fetch_user(payload.user_id)

                    info = {
                        'emoji': payload.emoji,
                        'user': user.name,
                        'message_id': message.id,
                        'channel_id': message.channel.id
                    }

                    # 创建交互记录
                    interaction = Interaction(
                        message_id=message.id,
                        channel_id=channel_id,
                        user_id=user.id,
                        username=user.name,
                        interaction_content='',
                        interaction_time=message.created_at,
                        post_time=message.created_at,
                        type=InteractionType.LIKE.value,
                        note=str(info)
                    )

                    self.db_service.save_channel_interaction(db, interaction)
                    self.logger.info(
                        f"Saved reaction: {user.name} reacted to message {message.id} with {payload.emoji}")
            except Exception as e:
                self.logger.error(f"Error processing reaction: {str(e)}")
            finally:
                db.close()

        except Exception as e:
            self.logger.error(f"Error in on_raw_reaction_add: {str(e)}")

    @staticmethod
    async def get_message_created_time(channel, message_id: int) -> Optional[datetime]:
        """
        获取指定消息的创建时间

        Args:
            channel: Discord channel对象
            message_id: 消息ID

        Returns:
            datetime: 消息的创建时间,如果消息不存在则返回None
        """
        try:
            message = await channel.fetch_message(message_id)
            return message.created_at + timedelta(milliseconds=1)  # 加1毫秒
        except Exception:
            return None
