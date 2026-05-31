"""Monotonic UUIDv7 generator (RFC 9562).

UUIDv7 embeds a 48-bit millisecond timestamp in the high bits, so values sort
chronologically. We add a per-process counter in the ``rand_a`` field so that
ids minted within the same millisecond are still strictly increasing — giving a
stable, gap-free ordering key for chat messages across both Postgres and SQLite.
"""

import os
import threading
import time
import uuid

_lock = threading.Lock()
_last_ms = 0
_counter = 0


def uuid7() -> uuid.UUID:
    global _last_ms, _counter
    with _lock:
        ms = int(time.time() * 1000)
        if ms <= _last_ms:
            ms = _last_ms
            _counter = (_counter + 1) & 0x0FFF  # 12-bit counter (rand_a)
        else:
            _last_ms = ms
            _counter = 0
        counter = _counter

    rand_b = int.from_bytes(os.urandom(8), "big") & ((1 << 62) - 1)
    value = (ms & ((1 << 48) - 1)) << 80
    value |= 0x7 << 76  # version
    value |= counter << 64  # rand_a (monotonic within a millisecond)
    value |= 0b10 << 62  # variant
    value |= rand_b
    return uuid.UUID(int=value)
