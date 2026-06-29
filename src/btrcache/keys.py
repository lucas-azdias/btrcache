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

__all__: typing.Final = ("HashedCacheKey",)


class HashedCacheKey:
    """Immutable tuple-like object that caches its computed hash value.

    The hash is computed lazily on first use and cached for subsequent
    calls to avoid repeated tuple hashing overhead in cache key generation.
    """

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
    __kwargs_marker: tuple[type] = (tuple,)

    def __init__(
        self,
        args: tuple[object, ...],
        kwargs: dict[str, object],
        *,
        is_typed: bool = False,
    ) -> None:
        """Initialize a hashable cache key from function arguments.

        This converts positional and keyword arguments into a single immutable
        tuple representation used for hashing and equality comparisons.

        Args:
            args (tuple[object, ...]):
                Positional arguments.

            kwargs (dict[str, object]):
                Keyword arguments.

            is_typed (bool):
                If True, include argument types in the generated key to
                distinguish values that compare equal but have different types.

        """
        self.__hashvalue: int
        self.__tuple: tuple[typing.Any, ...] = (
            self.__hashkey(args, kwargs) if not is_typed else self.__typed_hashkey(args, kwargs)
        )

    @typing.override
    def __eq__(self, value: object, /) -> bool:
        # Keys must share the same class
        if not isinstance(value, HashedCacheKey):
            return NotImplemented

        # If they share the same hash, must be the same key
        return self.__hash__() == value.__hash__()

    @typing.override
    def __hash__(self) -> int:
        # Try-except is used instead of `is None` for
        # performance issues
        try:
            return self.__hashvalue
        except AttributeError:
            # It will raise error if tuple has unhashable element
            self.__hashvalue = self.__tuple.__hash__()
            return self.__hashvalue

    @typing.override
    def __getstate__(self) -> object:
        # Only keeps the given arguments in pickle
        # (keeping hash stored is not safe)
        return self.__tuple

    def __setstate__(self, state: tuple[typing.Any, ...]) -> None:
        """Restore the object state during unpickling.

        This method reconstructs the internal immutable tuple representation
        from the serialized state. Any cached hash value is intentionally
        not restored, ensuring that the hash is recomputed lazily after
        unpickling if needed.

        Args:
            state (tuple[typing.Any, ...]):
                The previously serialized tuple representing the cache key.
                This contains only the semantic argument structure and does
                not include any runtime-cached values such as the hash.

        """
        # Restores internal tuple only
        self.__tuple = state

    @staticmethod
    def __hashkey(args: tuple[object, ...], kwargs: dict[str, object]) -> tuple[typing.Any, ...]:
        # No keyword arguments are present
        if not kwargs:
            return tuple(args)

        # Appends a marker followed by sorted keyword argument pairs to ensure
        # deterministic ordering and distinguish them from positional arguments
        return args + HashedCacheKey.__kwargs_marker + tuple(sorted(kwargs.items()))

    @staticmethod
    def __typed_hashkey(
        args: tuple[object, ...],
        kwargs: dict[str, object],
    ) -> tuple[typing.Any, ...]:
        # Starts with the positional argument values and appends
        # every value type to distinguish between them in the final
        # hash
        key = args + tuple(type(v) for v in args)

        if kwargs:
            # Sorts keyword arguments to produce a deterministic key
            sorted_kwargs = tuple(sorted(kwargs.items()))

            # Appends the sentinel marker and the keyword argument values
            key += HashedCacheKey.__kwargs_marker + sorted_kwargs

            # Append the type of each keyword argument value
            key += tuple(type(v) for _, v in sorted_kwargs)

        return key
