import json
import logging
import urllib.parse
import uuid

from pynostr.event import Event
from pynostr.filters import FiltersList, Filters
from pynostr.key import PrivateKey
from pynostr.relay_manager import RelayManager

from app.models.models import Interaction, InteractionType
from app.services.database_service import DatabaseService

log = logging.getLogger(__name__)


class NostrSync:

    def __init__(self, relay_url, private_key: str):
        if not relay_url:
            raise ValueError("Relay URL is required")

        self.relay_manager = RelayManager(timeout=6)
        for relay in relay_url:
            # 需要将relay进行url解析， 看是否是wss的还是ws的
            parsed_url = urllib.parse.urlparse(relay)
            if parsed_url.scheme not in ['ws', 'wss']:
                raise ValueError(f"Invalid relay URL scheme: {parsed_url.scheme}")
            self.relay_manager.add_relay(relay, close_on_eose=False)

        private_pair = PrivateKey.from_nsec(private_key)
        self.private_pair = private_pair
        filters = FiltersList([Filters(authors=[private_pair.public_key.hex()], limit=100)])
        subscription_id = uuid.uuid1().hex
        self.relay_manager.add_subscription_on_all_relays(subscription_id, filters)

        self.db_service = DatabaseService()

    def sync_interactions(self, interactions):
        for interaction in interactions:
            event = self.create_nostr_event(interaction)
            self.relay_manager.publish_event(event)
            self.relay_manager.run_sync()

            while self.relay_manager.message_pool.has_ok_notices():
                ok_msg = self.relay_manager.message_pool.get_ok_notice()
                self.db_service.update_interaction_published_status(interaction.interaction_id, ok_msg['event_id'])

    # def 一个只用于测试的方法
    def test_sync_interactions(self, event):
        self.relay_manager.publish_event(event)
        self.relay_manager.run_sync()

        while self.relay_manager.message_pool.has_ok_notices():
            ok_msg = self.relay_manager.message_pool.get_ok_notice()
            print(ok_msg)

    def create_nostr_event(self, interaction: Interaction) -> Event:
        """
        [
            "EVENT",
            {
                "id": "<事件唯一ID>",
                "pubkey": "<TEE节点公钥>",
                "created_at": "<TEE节点同步时间戳>",
                "kind": 1,
                "tags": [
                    ["t", "discord"],  // 标识事件来源于Discord
                    ["channel_id", "<Discord频道ID>"],  // 发言所在的频道ID
                    ["user_id", "<发言用户Discord ID>"],  // 发言用户的ID
                    ["created_at", "<发言时间>"],
                    ["username", "<发言用户用户名>"],  // 发言用户的用户名
                    ["message_id", "<原消息ID>"]  // 原始发言消息的ID
                ],
                "content": "<发言内容>",
                "sig": "<事件签名>"
            }
        ]
        """
        if interaction.type == InteractionType.RETWEET.value or InteractionType.REPLY.value:
            return self.create_nostr_retweet_event(interaction)
        elif interaction.type == InteractionType.LIKE.value:
            return self.create_nostr_like_event(interaction)
        tags = [
            ['t', 'discord'],
            ['channel_id', str(interaction.channel_id)],
            ['user_id', interaction.user_id],
            ["created_at", str(int(interaction.interaction_time.timestamp()))],
            ["message_id", interaction.message_id],
            ['username', interaction.username]
        ]
        event = Event(interaction.interaction_content)
        for tag in tags:
            event.add_tag(tag[0], tag[1])
        event.sign(self.private_pair.hex())
        return event

    def create_nostr_retweet_event(self, interaction: Interaction) -> Event:
        """
        {
            "id": "<事件唯一ID>",
            "pubkey": "<TEE节点公钥>",
            "created_at": "<TEE节点同步时间戳>",
            "kind": 6,
            "tags": [
                ["t", "discord"],  // 标识事件来源于Discord
                ["channel_id", "<Discord频道ID>"],  // 转发所在的频道ID
                ["user_id", "<转发用户Discord ID>"],  // 转发用户的ID
                ["username", "<转发用户用户名>"],  // 转发用户的用户名
                ["created_at", "<转发时间>"],
                ["message_id", "<被转发消息ID>"],  // 被转发消息的ID
                ["e", "<被转发消息的事件ID>"]  // 被转发消息的Nostr事件ID
            ],
            "content": "",
            "sig": "<事件签名>"
        }
        """
        tags = [
            ['t', 'discord'],
            ['channel_id', str(interaction.channel_id)],
            ['user_id', interaction.user_id],
            ["created_at", str(int(interaction.interaction_time.timestamp()))],
            ["message_id", interaction.message_id],
            ['username', interaction.username],
        ]
        event = Event("", kind=6)
        for tag in tags:
            event.add_tag(tag[0], tag[1])
        # 从interaction.note字符串中通过json解析出来对应的channel_id和message_id
        note_data = json.loads(interaction.note)
        channel_id = note_data.get('channel_id')
        message_id = note_data.get('message_id')
        event_id = self.db_service.get_interaction_nostr_event_id(channel_id, message_id)
        if event_id:
            event.add_tag('e', event_id)
        event.sign(self.private_pair.hex())
        return event

    def create_nostr_like_event(self, interaction: Interaction) -> Event:
        """
        {
            "id": "<事件唯一ID>",
            "pubkey": "<TEE节点公钥>",
            "created_at": "<TEE节点同步时间戳>",
            "kind": 7,
            "tags": [
                ["t", "discord"],  // 标识事件来源于Discord
                ["channel_id", "<Discord频道ID>"],  // 反应所在的频道ID
                ["user_id", "<反应用户Discord ID>"],  // 反应用户的ID
                ["username", "<反应用户用户名>"],  // 反应用户的用户名
                ["created_at", "<点赞时间>"],
                ["message_id", "<被反应的消息ID>"],  // 被反应的消息ID
                ["e", "<被反应消息的Nostr事件ID>"],  // 被反应消息的Nostr事件ID
                ["reaction", "<反应类型，如👍>"]  // 反应的具体内容（如emoji）
            ],
            "content": "",
            "sig": "<事件签名>"
        }
        """
        tags = [
            ['t', 'discord'],
            ['channel_id', str(interaction.channel_id)],
            ['user_id', interaction.user_id],
            ["created_at", str(int(interaction.interaction_time.timestamp()))],
            ["message_id", interaction.message_id],
            ['username', interaction.username],
        ]
        event = Event("", kind=7)
        for tag in tags:
            event.add_tag(tag[0], tag[1])
        # 从interaction.note字符串中通过json解析出来对应的channel_id和message_id
        note_data = json.loads(interaction.note)
        channel_id = note_data.get('channel_id')
        message_id = note_data.get('message_id')
        emoji = note_data.get('emoji')
        event_id = self.db_service.get_interaction_nostr_event_id(channel_id, message_id)
        if event_id:
            event.add_tag('e', event_id)
        if emoji:
            event.add_tag('reaction', emoji)
        event.sign(self.private_pair.hex())
        return event
