#!/usr/bin/env python

import uuid

import tornado.ioloop
from pynostr.base_relay import RelayPolicy
from pynostr.event import EventKind
from pynostr.filters import Filters, FiltersList
from pynostr.key import PublicKey
from pynostr.message_pool import MessagePool
from pynostr.relay import Relay
from pynostr.utils import get_public_key
from rich.console import Console
from rich.table import Table
from tornado import gen

if __name__ == "__main__":

    console = Console(width=10000)

    input_str = "npub1evn8kd65v4whrkqrust8r6y77keamkwyk3yuxlvc9lc9jant7jwq8qp0lv"
    recipient = ""
    author = get_public_key(input_str)

    relay_url = 'ws://144.126.138.135:10548'

    filters = FiltersList(
        [Filters(authors=[author.hex()], kinds=[EventKind.TEXT_NOTE], limit=100)]
        # [Filters(kinds=[EventKind.TEXT_NOTE], limit=100)]
    )

    subscription_id = uuid.uuid1().hex
    io_loop = tornado.ioloop.IOLoop.current()
    message_pool = MessagePool(first_response_only=False)
    policy = RelayPolicy()
    r = Relay(relay_url, message_pool, io_loop, policy, timeout=3)

    r.add_subscription(subscription_id, filters)

    try:
        io_loop.run_sync(r.connect)
    except gen.Return:
        pass
    io_loop.stop()

    event_msgs = message_pool.get_all_events()
    print(f"{r.url} returned {len(event_msgs)} TEXT_NOTEs from {input_str}.")

    table = Table("date", "content", "author", width=200)
    for event_msg in event_msgs[::-1]:
        table.add_row(str(event_msg.event.date_time()), event_msg.event.content, PublicKey.from_hex(event_msg.event.pubkey).npub)
    console.print(table)
