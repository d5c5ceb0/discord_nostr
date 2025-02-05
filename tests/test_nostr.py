from datetime import datetime

from app.models.interaction import Interaction
from app.services.pynostr_sync import NostrSync
from config.config import Config


def test_publish_mock_interaction():
    # Initialize NostrSync object
    # relay_urls = ['wss://relay.mostr.pub', 'wss://offchain.pub']
    relay_urls = ["ws://144.126.138.135:10548"]
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
    nostr_sync.test_sync_interactions(event)