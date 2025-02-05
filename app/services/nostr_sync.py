# import logging
# import ssl
# import time
# import urllib.parse
#
# from nostr.event import Event, EventKind
# from nostr.relay_manager import RelayManager
# from nostr.key import PrivateKey
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
#         self.relay_manager = RelayManager()
#         for relay in relay_url:
#             # 需要将relay进行url解析， 看是否是wss的还是ws的
#             parsed_url = urllib.parse.urlparse(relay)
#             if parsed_url.scheme not in ['ws', 'wss']:
#                 raise ValueError(f"Invalid relay URL scheme: {parsed_url.scheme}")
#             self.relay_manager.add_relay(relay, close_on_eose=False)
#         ssl_opt = {
#             "cert_reqs": ssl.CERT_NONE,  # 不验证服务器证书
#             "check_hostname": False,     # 不检查主机名
#             "ca_certs": None             # 不使用CA证书
#         }
#         self.relay_manager.open_connections(ssl_opt)
#         time.sleep(1.25) # allow the connections to open
#
#         while self.relay_manager.message_pool.has_notices():
#             notice_msg = self.relay_manager.message_pool.get_notice()
#             log.info(notice_msg.content)
#
#         private_pair = PrivateKey.from_nsec(private_key)
#         self.private_pair = private_pair
#         self.public_key = private_pair.public_key
#         self.db_service = DatabaseService()
#
#     def sync_interactions(self):
#         relay_manager = self.relay_manager
#         total, interactions = self.db_service.get_unsynced_interactions()
#         for interaction in interactions:
#             event = self.create_nostr_event(interaction)
#             time.sleep(1) # allow the messages to send
#             relay_manager.publish_event(event)
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
#         event = Event(
#             kind=EventKind.TEXT_NOTE,
#             tags=tags,
#             content=interaction.interaction_content,
#             public_key=self.public_key.hex(),
#             created_at=int(interaction.interaction_time.timestamp()),
#             signature=None
#         )
#         self.private_pair.sign_event(event)
#         return event
#
