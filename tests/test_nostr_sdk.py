import json
import time
from ctypes import cast
from datetime import datetime

from nostr_sdk.nostr_sdk import Filter, KindEnum, ClientMessageEnum, Kind

from app.models.interaction import Interaction
from app.services.nostr_sdk_sync import NostrSync
from config.config import Config


def test_publish_mock_interaction():
    # Initialize NostrSync object
    relay_urls = ['wss://relay.mostr.pub', 'wss://offchain.pub']
    # relay_urls = ['ws://144.126.138.135:10548']
    private_key = Config.NOSTR_PRIVATE_KEY
    nostr_sync = NostrSync(relay_urls, private_key)

    # Create a mock Interaction object
    mock_interaction = Interaction(
        channel_id='mock_channel_id',
        user_id='mock_user_id',
        interaction_time=datetime.now(),
        username='mock_username',
        interaction_content='This is a mock interaction content',
        message_id='mock_message_id'
    )
    # Create and publish event
    event = nostr_sync.create_nostr_event(mock_interaction)
    relay_manager = nostr_sync.relay_manager

    relay_manager.publish_event(event)
    time.sleep(5)  # allow the messages to send

    filters = Filter()
    filters.authors([nostr_sync.private_pair.public_key()])
    filters.kinds([Kind.from_enum(cast(KindEnum, KindEnum.TEXT_NOTE()))])
    subscription_id = "test_subscription_id"
    request = [ClientMessageEnum.REQ, subscription_id]
    request.extend(filters.as_json())

    message = json.dumps(request)
    relay_manager.publish_message(message)
    time.sleep(1) # allow the messages to send

    while relay_manager.message_pool.has_events():
        event_msg = relay_manager.message_pool.get_event()
        print(event_msg.event.content)

    relay_manager.close_connections()