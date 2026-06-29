# Copyright (C) 2026 Lucas Dias
#
# Portions Copyright (C) 2026 Thomas Kemmer
# Source: https://github.com/tkem/cachetools/blob/48284d73d0a8834c9c50f8d41bb99e6f93b2dfed/src/cachetools/keys.py
# License: MIT (See LICENSE file for details)

"""Utilities for constructing hashable cache keys.

This module provides helper functions for converting function arguments
into immutable, hashable objects suitable for use as cache keys.
"""

import typing

if typing.TYPE_CHECKING:
    import collections.abc

__all__: typing.Final = ("hashkey", "typedkey")


class __HashedTuple(tuple[typing.Any, ...]):
    """Tuple subclass that caches its computed hash value."""

    __slots__ = ("__hashvalue",)

    __hashvalue: int

    @typing.override
    def __hash__(self) -> int:
        try:
            return self.__hashvalue
        except AttributeError:
            # IGNORE: Generic resolution in `tuple` was ignored for
            # performance issues, as it would be necessary to use
            # `super().__class__` instead.
            self.__hashvalue = self.__hashvalue = tuple.__hash__(self)  # pyright: ignore[reportUnknownMemberType]
            return self.__hashvalue

    @typing.override
    def __getstate__(self) -> object:
        # Indicates that no additional instance state exists for pickling
        return None


# Sentinel marker used to separate positional arguments from keyword arguments
# when building cache keys.
#
# This prevents ambiguity between calls like:
#     f(1, ("x", 2))        -> positional tuple argument
#     f(1, x=2)             -> keyword argument form
#
# Without a separator, both could normalize to the same tuple representation,
# causing cache key collisions.
#
# The value is a class object because it is guaranteed unique, immutable and hashable.
__kwargs_marker = (__HashedTuple,)


def hashkey(*args: object, **kwargs: object) -> collections.abc.Hashable:
    """Build a hashable cache key from function arguments.

    Positional arguments are stored in their original order. Keyword
    arguments are sorted by name and appended after a unique sentinel value,
    ensuring deterministic keys and preventing collisions with positional
    arguments.

    Args:
        *args (object):
            Positional arguments.

        **kwargs (object):
            Keyword arguments.

    Returns:
        Hashable:
            A hashable object suitable for use as a cache key.

    """
    # No keyword arguments are present
    if not kwargs:
        return __HashedTuple(args)

    # Appends a marker followed by sorted keyword argument pairs to ensure
    # deterministic ordering and distinguish them from positional arguments
    return __HashedTuple(args + __kwargs_marker + tuple(sorted(kwargs.items())))


def typedkey(*args: object, **kwargs: object) -> collections.abc.Hashable:
    """Build a type-sensitive hashable cache key.

    In addition to argument values, the type of every positional and keyword
    argument is included in the generated key. This distinguishes arguments
    that compare equal but have different types.

    Args:
        *args (object):
            Positional arguments.

        **kwargs (object):
            Keyword arguments.

    Returns:
        Hashable:
            A hashable object that uniquely represents both the values and
            types of the supplied arguments.

    """
    # Starts with the positional argument values and appends
    # every value type to distinguish between them in the final
    # hash
    key = args + tuple(type(v) for v in args)

    if kwargs:
        # Sorts keyword arguments to produce a deterministic key
        sorted_kwargs = tuple(sorted(kwargs.items()))

        # Appends the sentinel marker and the keyword argument values
        key += __kwargs_marker + sorted_kwargs

        # Append the type of each keyword argument value
        key += tuple(type(v) for _, v in sorted_kwargs)

    return __HashedTuple(key)
