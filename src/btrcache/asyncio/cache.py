# Copyright (C) 2026 Lucas Dias

"""Type aliases for asynchronous cache implementations.

This module defines generic cache aliases used by the asynchronous
decorators.
"""

import asyncio
import typing

from src.btrcache.cache import Cache

__all__: typing.Final = ("AsyncCache",)

# Each asynchronous cache entry stores the executing `Task`
# together with the shared `Future` returned
type AsyncCache[R] = Cache[tuple[asyncio.Task[R], asyncio.Future[R]]]
