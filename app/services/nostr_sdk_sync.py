# import json
# import logging
# import ssl
# import time
# import urllib.parse
#
# from nostr_sdk import Keys, Client, Event, EventBuilder
#
# from app.models.interaction import Interaction
# from app.services.database_service import DatabaseService
#
# log = logging.getLogger(__name__)
#
# class NostrSync:
#
#     def __init__(self, relay_url, private_key:str):
#         if not relay_url:
#             raise ValueError("Relay URL is required")
#
#         self.client = Client()
#         for relay in relay_url:
#             # 需要将relay进行url解析， 看是否是wss的还是ws的
#             parsed_url = urllib.parse.urlparse(relay)
#             if parsed_url.scheme not in ['ws', 'wss']:
#                 raise ValueError(f"Invalid relay URL scheme: {parsed_url.scheme}")
#             self.client.add_relay(relay)
#         self.client.connect()
#
#         private_pair = Keys.parse(private_key)
#         self.private_pair = private_pair
#         self.public_key = private_pair.public_key()
#         self.db_service = DatabaseService()
#
#     def sync_interactions(self):
#         client = self.client
#         total, interactions = self.db_service.get_unsynced_interactions()
#         for interaction in interactions:
#             event = self.create_nostr_event(interaction)
#             time.sleep(1) # allow the messages to send
#             client.send_event(event)
#
#     def create_nostr_event(self, interaction: Interaction) -> Event:
#         """
#         [
#             "EVENT",
#             {
#                 "id": "<事件唯一ID>",
#                 "pubkey": "<TEE节点公钥>",
#                 "created_at": "<TEE节点同步时间戳>",
#                 "kind": 1,
#                 "tags": [
#                     ["t", "discord"],  // 标识事件来源于Discord
#                     ["channel_id", "<Discord频道ID>"],  // 发言所在的频道ID
#                     ["user_id", "<发言用户Discord ID>"],  // 发言用户的ID
#                     ["created_at", "<发言时间>"],
#                     ["username", "<发言用户用户名>"],  // 发言用户的用户名
#                     ["message_id", "<原消息ID>"]  // 原始发言消息的ID
#                 ],
#                 "content": "<发言内容>",
#                 "sig": "<事件签名>"
#             }
#         ]
#         """
#         tags = [
#             ['t', 'discord'],
#             ['channel_id', interaction.channel_id],
#             ['user_id', interaction.user_id],
#             ["created_at", int(interaction.interaction_time.timestamp())],
#             ["message_id", interaction.message_id],
#             ['username', interaction.username]
#         ]
#         event = EventBuilder.text_note(interaction.interaction_content).tags(tags).custom_created_at(int(interaction.interaction_time.timestamp())).sign_with_keys(self.private_pair)
#         return event
#
