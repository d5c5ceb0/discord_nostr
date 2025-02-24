import pytz
from sqlalchemy import func
from sqlalchemy.orm import Session
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any, Tuple

from app.models.models import Channel, Interaction, ChannelCollectLog


class DatabaseService:
    @staticmethod
    def get_active_channels(db: Session) -> List[Channel]:
        return db.query(Channel).all()

    @staticmethod
    def select_max_interaction_id(db: Session, channel_id: int) -> Optional[int]:
        result = db.query(Interaction.message_id) \
            .filter(Interaction.channel_id == channel_id) \
            .order_by(Interaction.post_time.desc()) \
            .first()
        return result[0] if result else None

    @staticmethod
    def get_interaction_nostr_event_id(db: Session, channel_id: int, message_id: int) -> Optional[str]:
        result = db.query(Interaction.nostr_event_id) \
            .filter(Interaction.channel_id == channel_id) \
            .filter(Interaction.message_id == message_id) \
            .first()
        return result[0] if result else None

    @staticmethod
    def update_interaction_published_status(db: Session, interaction_id: int, nostr_event_id: str) -> bool:
        interaction = db.query(Interaction) \
            .filter(Interaction.interaction_id == interaction_id) \
            .first()

        if not interaction:
            return False

        interaction.nostr_event_id = nostr_event_id
        interaction.is_published = True

        try:
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise

    @staticmethod
    def save_interactions_batch(db: Session, interactions: List[Dict[str, Any]]) -> int:
        interaction_objects = []
        for item in interactions:
            interaction = Interaction(
                message_id=item['message_id'],
                channel_id=item['channel_id'],
                user_id=item['user_id'],
                username=item['username'],
                interaction_content=item['interaction_content'],
                interaction_time=item['interaction_time'],
                post_time=item['post_time'],
                note=item['note'],
                type=item['type']
            )
            interaction_objects.append(interaction)

        try:
            db.bulk_save_objects(interaction_objects)
            db.commit()
            return len(interaction_objects)
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def get_channel_interaction_count(db: Session, channel_id: int) -> int:
        channel = db.query(Channel).filter(Channel.channel_id == channel_id).first()

        if channel and channel.expiration_time:
            cutoff_time = DatabaseService.parse_expiration_time(channel.expiration_time)
            return db.query(Interaction) \
                .filter(Interaction.channel_id == channel_id) \
                .filter(Interaction.collect_time > cutoff_time) \
                .count()

        return db.query(Interaction) \
            .filter(Interaction.channel_id == channel_id) \
            .count()

    @staticmethod
    def get_user_interaction_stats(db: Session, user_id: str, start_time: int, end_time: int) -> Tuple[int, List[Dict]]:
        # 获取所有有效频道
        channels = db.query(Channel).all()

        if not channels:
            return 0, []

        total = 0
        result = []

        for channel in channels:
            query = db.query(func.count(Interaction.interaction_id)) \
                .filter(
                Interaction.user_id == user_id,
                Interaction.channel_id == channel.channel_id
            )
            if start_time:
                query = query.filter(Interaction.collect_time > datetime.fromtimestamp(start_time, pytz.UTC))
            if end_time:
                query = query.filter(Interaction.collect_time < datetime.fromtimestamp(end_time, pytz.UTC))

            count = query.scalar()

            if count > 0:
                total += count
                result.append({'channel_id': channel.channel_id, 'count': count})

        return total, result

    @staticmethod
    def get_channel_last_collect_time(db: Session, channel_id: int) -> Optional[datetime]:
        result = db.query(func.max(ChannelCollectLog.collect_time)) \
            .filter(ChannelCollectLog.channel_id == channel_id) \
            .scalar()
        return result

    @staticmethod
    def save_channel_collect_log(db: Session, channel_id: int,
                                 collect_start_time: datetime,
                                 collect_end_time: datetime) -> int:
        log = ChannelCollectLog(
            channel_id=channel_id,
            collect_status=1,
            collect_error_message='',
            collect_start_time=collect_start_time,
            collect_end_time=collect_end_time
        )
        db.add(log)
        db.commit()
        db.refresh(log)
        return log.id

    @staticmethod
    def get_unsynced_interactions(db: Session) -> Tuple[int, List[Interaction]]:
        interactions = db.query(Interaction) \
            .filter(Interaction.is_published == False) \
            .all()
        return len(interactions), interactions

    @classmethod
    @staticmethod
    def add_channel(db: Session, validated_data: Dict[str, Any]) -> int:
        # 检查channel_id是否已存在
        existing_channel = db.query(Channel) \
            .filter(Channel.channel_id == validated_data['channel_id']) \
            .first()
        if existing_channel:
            raise ValueError(f"Channel ID {validated_data['channel_id']} already exists")

        # 创建新的Channel对象
        channel = Channel(
            channel_id=validated_data['channel_id'],
            collect_start_time=validated_data.get('start_time'),
            collect_end_time=validated_data.get('end_time'),
            update_frequency=validated_data.get('update_frequency'),
            expiration_time=validated_data.get('expiration_time')
        )

        try:
            db.add(channel)
            db.commit()
            db.refresh(channel)
            return channel.id
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def update_channel(db: Session, validated_data: Dict[str, Any]) -> bool:
        channel = db.query(Channel) \
            .filter(Channel.channel_id == validated_data['channel_id']) \
            .first()

        if not channel:
            return False

        # 更新字段映射
        field_map = {
            'start_time': 'collect_start_time',
            'end_time': 'collect_end_time',
            'update_frequency': 'update_frequency',
            'expiration_time': 'expiration_time'
        }

        # 更新字段
        for key, field_name in field_map.items():
            if key in validated_data:
                setattr(channel, field_name, validated_data[key])

        try:
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def delete_channel(db: Session, validated_data: Dict[str, Any]) -> bool:
        channel = db.query(Channel) \
            .filter(Channel.channel_id == validated_data['channel_id']) \
            .first()

        if not channel:
            return False

        try:
            db.delete(channel)
            db.commit()
            return True
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def get_channel(db: Session, channel_id: int) -> Optional[Dict]:
        channel = db.query(Channel) \
            .filter(Channel.channel_id == channel_id) \
            .first()

        if not channel:
            return None

        return {
            'id': channel.id,
            'channel_id': channel.channel_id,
            'collect_start_time': channel.collect_start_time,
            'collect_end_time': channel.collect_end_time,
            'update_frequency': channel.update_frequency,
            'expiration_time': channel.expiration_time,
            'create_at': channel.create_at,
            'update_at': channel.update_at
        }

    @staticmethod
    def save_channel_interaction(db: Session, interaction: Interaction):
        try:
            db.add(interaction)
            db.commit()
        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def parse_expiration_time(expiration_time: str) -> datetime:
        """
        Parse expiration time string and calculate the cutoff datetime
        """
        if not expiration_time or not isinstance(expiration_time, str):
            raise ValueError("Expiration time must not be empty and must be a string")

        expiration_time = expiration_time.strip().lower()

        if len(expiration_time) < 2:
            raise ValueError("Invalid expiration time format")

        try:
            number = int(expiration_time[:-1])
            unit = expiration_time[-1]
        except ValueError:
            raise ValueError("Invalid number format")

        time_units = {
            'd': 1,
            'w': 7,
            'm': 30,
            'y': 365
        }

        if unit not in time_units:
            raise ValueError("Invalid time unit, must be d (day), w (week), m (month), or y (year)")

        if number <= 0:
            raise ValueError("Time value must be greater than 0")

        total_days = number * time_units[unit]
        return datetime.now() - timedelta(days=total_days)

    @staticmethod
    def get_user_interaction_history(db: Session, 
                                   user_id: str, 
                                   channel_id: str = None, 
                                   offset: int = 0, 
                                   limit: int = 10) -> Tuple[int, List[Dict[str, Any]]]:
        """
        获取用户互动历史
        
        Args:
            db: 数据库会话
            user_id: 用户ID
            channel_id: 频道ID (可选)
            offset: 分页偏移量
            limit: 分页大小
            
        Returns:
            Tuple[消息数量, 消息列表]
        """
        query = db.query(Interaction)\
            .filter(Interaction.user_id == user_id)\
            .order_by(Interaction.interaction_time.desc())

        if channel_id:
            query = query.filter(Interaction.channel_id == channel_id)

        # 获取总数
        total_count = query.count()

        # 应用分页
        messages = query.offset(offset).limit(limit).all()

        # 格式化返回数据
        formatted_messages = [{
            'channel_id': msg.channel_id,
            'message': msg.interaction_content,
            'timestamp': msg.interaction_time.strftime('%a, %d %b %Y %H:%M:%S -0000')
        } for msg in messages]

        return total_count, formatted_messages

    @staticmethod
    def get_interaction_history(db: Session,
                                   channel_id: str = None,
                                   offset: int = 0,
                                   limit: int = 10,
                                   start_time: int = None,
                                   end_time: int = None
                                ) -> Tuple[int, List[Dict[str, Any]]]:
        """
        获取用户互动历史

        Args:
            db: 数据库会话
            channel_id: 频道ID (可选)
            offset: 分页偏移量
            limit: 分页大小

        Returns:
            Tuple[消息数量, 消息列表]
        """
        query = db.query(Interaction)\
            .order_by(Interaction.interaction_time.desc())

        if channel_id:
            query = query.filter(Interaction.channel_id == channel_id)

        if start_time:
            query = query.filter(Interaction.collect_time > datetime.fromtimestamp(start_time, pytz.UTC))
        if end_time:
            query = query.filter(Interaction.collect_time < datetime.fromtimestamp(end_time, pytz.UTC))


        # 获取总数
        total_count = query.count()

        # 应用分页
        messages = query.offset(offset).limit(limit).all()

        # 格式化返回数据
        formatted_messages = [{
            'user_id': msg.user_id,
            'channel_id': msg.channel_id,
            'message': msg.interaction_content,
            'timestamp': msg.interaction_time.strftime('%a, %d %b %Y %H:%M:%S -0000')
        } for msg in messages]

        return total_count, formatted_messages
