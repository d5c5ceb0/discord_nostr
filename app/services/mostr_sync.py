# import asyncio
# import logging
# from datetime import datetime
#
# from monstr.client.client import Client
# from monstr.encrypt import Keys
# from monstr.event.event import Event
#
# from app.models.interaction import Interaction
# from app.services.database_service import DatabaseService
# from config.config import Config
#
# log = logging.getLogger(__name__)
#
#
# class NostrSync:
#
#     def __init__(self, relay_urls, private_key: str):
#         if not relay_urls:
#             raise ValueError("Relay URLs are required")
#
#         self.relay_urls = relay_urls
#         self.private_pair = Keys(priv_k=private_key)
#         self.db_service = DatabaseService()
#
#     async def do_post(self, url, evt: Event):
#         async with Client(url) as c:
#             evt.sign(self.private_pair.private_key_hex())
#             c.publish(evt)
#
#             # Kind 4 for NIP4, NIP44 has no set kind so will depend
#             # evt.kind = Event.KIND_ENCRYPT
#
#             # # Same NIP4 encrypted
#             # my_enc = NIP4Encrypt(self.private_pair)  # or NIP44Encrypt(n_keys)
#             # # Returns event with to_p_tag and content encrypted
#             # n_msg = my_enc.encrypt_event(evt=n_msg, to_pub_k=self.private_pair.public_key_hex())
#             #
#             # n_msg.sign(self.private_pair.private_key_hex())
#             # c.publish(n_msg)
#
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
#             ["t", "discord"],
#             ["channel_id", str(interaction.channel_id)],
#             ["user_id", str(interaction.user_id)],
#             ["created_at", int(interaction.interaction_time.timestamp())],
#             ["username", interaction.username],
#             ["message_id", str(interaction.message_id)]
#         ]
#         event = Event(
#             kind=Event.KIND_TEXT_NOTE,
#             tags=tags,
#             content=interaction.interaction_content,
#             pub_key=self.private_pair.public_key_hex(),
#             created_at=int(interaction.interaction_time.timestamp()),
#             sig=None
#         )
#         return event
#
#     async def sync_relays(self, event: Event):
#         for url in self.relay_urls:
#             await self.do_post(url, event)
#
#     async def sync_interactions(self):
#         total, interactions = self.db_service.get_unsynced_interactions()
#         for interaction in interactions:
#             for url in self.relay_urls:
#                 await self.do_post(url, self.create_nostr_event(interaction))
#
#
# if __name__ == '__main__':
#     relay_urls = ['wss://offchain.pub']
#     private_key = Config.NOSTR_PRIVATE_KEY
#     nostr_sync = NostrSync(relay_urls, private_key)
#
#     # Create a mock Interaction object
#     mock_interaction = Interaction(
#         channel_id='mock_channel_id',
#         user_id='mock_user_id',
#         interaction_time=datetime.now(),
#         username='mock_username',
#         interaction_content='This is a mock interaction content',
#         message_id='mock_message_id',
#     )
#     # Create and publish event
#     event = nostr_sync.create_nostr_event(mock_interaction)
#     event.sign(nostr_sync.private_pair.private_key_hex())
#
#     asyncio.run(nostr_sync.sync_relays(event))