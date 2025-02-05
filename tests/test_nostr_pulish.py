import time
import uuid

from pynostr.event import Event
from pynostr.filters import FiltersList, Filters
from pynostr.key import PrivateKey
from pynostr.relay_manager import RelayManager

from config.config import Config


def test_publish():
    relay_manager = RelayManager(timeout=6)
    relay_manager.add_relay("ws://144.126.138.135:10548", close_on_eose=False)
    private_key = PrivateKey.from_nsec(Config.NOSTR_PRIVATE_KEY)

    filters = FiltersList([Filters(authors=[private_key.public_key.hex()], limit=100)])
    subscription_id = uuid.uuid1().hex
    relay_manager.add_subscription_on_all_relays(subscription_id, filters)

    event = Event("This is a publish interaction content")
    event.sign(private_key.hex())

    relay_manager.publish_event(event)
    relay_manager.run_sync()
    time.sleep(5) # allow the messages to send
    while relay_manager.message_pool.has_ok_notices():
        ok_msg = relay_manager.message_pool.get_ok_notice()
        print(ok_msg)
    while relay_manager.message_pool.has_events():
        event_msg = relay_manager.message_pool.get_event()
        print(event_msg.event.to_dict())
