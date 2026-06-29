# Copyright (C) 2026 Lucas Dias

"""Cache collections and related abstractions.

This module provides shared cache collection interfaces, generic type
aliases, and cache implementations.
"""

import typing

from src.btrcache.keys import HashedKey

if typing.TYPE_CHECKING:
    import collections.abc

__all__: typing.Final = ("Cache",)

type Cache[R] = collections.abc.MutableMapping[
    HashedKey,
    R,
]
