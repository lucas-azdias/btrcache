# Copyright (C) 2026 Lucas Dias
#
# Portions Copyright (C) 2026 Thomas Kemmer
# Source: https://github.com/tkem/cachetools/blob/48284d73d0a8834c9c50f8d41bb99e6f93b2dfed/src/cachetools/keys.py
# License: MIT (See LICENSE file for details)

"""Utilities for constructing deterministic, hashable cache keys.

This module provides strategies for converting positional and keyword
arguments into immutable tuple representations suitable for hashing and
cache lookups, along with a lightweight wrapper that lazily caches the
computed hash value.
"""

import typing

__all__: typing.Final = (
    "HashedKey",
    "KeyHashStrategy",
    "KeyHashStrategyProtocol",
    "KeyHashTypedStrategy",
)

# Immutable tuple representation used internally for cache keys.
type RawCacheKey = tuple[typing.Any, ...]


class KeyHashStrategyProtocol(typing.Protocol):
    """Protocol implemented by cache key generation strategies."""

    @staticmethod
    def hashkey(args: tuple[object, ...], kwargs: dict[str, object]) -> RawCacheKey:
        """Convert function arguments into a hashable cache key.

        Args:
            args (tuple[object, ...]):
                Positional arguments.

            kwargs (dict[str, object]):
                Keyword arguments.

        Returns:
            RawCacheKey:
                Immutable tuple representing the cache key.

        """
        raise NotImplementedError


class KeyHashStrategy:
    """Generate cache keys using only argument values."""

    @staticmethod
    def hashkey(args: tuple[object, ...], kwargs: dict[str, object]) -> RawCacheKey:
        """Construct a deterministic cache key.

        Positional arguments are stored first. Keyword arguments are
        sorted by name and appended after a sentinel marker to ensure
        deterministic ordering and avoid ambiguity with positional
        arguments.

        Args:
            args (tuple[object, ...]):
                Positional arguments.

            kwargs (dict[str, object]):
                Keyword arguments.

        Returns:
            RawCacheKey:
                Immutable tuple representing the cache key.

        """
        # No keyword arguments are present
        if not kwargs:
            return tuple(args)

        # Appends a marker followed by sorted keyword argument pairs to ensure
        # deterministic ordering and distinguish them from positional arguments
        return args + HashedKey.KWARGS_MARKER + tuple(sorted(kwargs.items()))


class KeyHashTypedStrategy:
    """Generate cache keys that also encode argument types."""

    @staticmethod
    def hashkey(args: tuple[object, ...], kwargs: dict[str, object]) -> RawCacheKey:
        """Construct a type-aware cache key.

        In addition to argument values, the runtime type of each argument
        is appended to distinguish values that compare equal but have
        different types.

        Args:
            args (tuple[object, ...]):
                Positional arguments.

            kwargs (dict[str, object]):
                Keyword arguments.

        Returns:
            RawCacheKey:
                Immutable tuple representing the cache key.

        """
        # Starts with the positional argument values and appends
        # every value type to distinguish between them in the final
        # hash
        key = args + tuple(type(v) for v in args)

        if kwargs:
            # Sorts keyword arguments to produce a deterministic key
            sorted_kwargs = tuple(sorted(kwargs.items()))

            # Appends the sentinel marker and the keyword argument values
            key += HashedKey.KWARGS_MARKER + sorted_kwargs

            # Append the type of each keyword argument value
            key += tuple(type(v) for _, v in sorted_kwargs)

        return key


class HashedKey:
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
    KWARGS_MARKER: typing.ClassVar[tuple[type]] = (tuple,)

    def __init__(
        self,
        args: tuple[object, ...],
        kwargs: dict[str, object],
        *,
        hash_strategy: KeyHashStrategyProtocol = KeyHashStrategy,
    ) -> None:
        """Initialize a hashable cache key from function arguments.

        This converts positional and keyword arguments into a single immutable
        tuple representation used for hashing and equality comparisons.

        Args:
            args (tuple[object, ...]):
                Positional arguments.

            kwargs (dict[str, object]):
                Keyword arguments.

            hash_strategy (KeyHashStrategyProtocol):
                Strategy used to normalize the arguments into an immutable cache
                key representation.

        """
        self.__hashvalue: int
        self.__tuple: RawCacheKey = hash_strategy.hashkey(args, kwargs)

    @typing.override
    def __eq__(self, value: object, /) -> bool:
        # Keys must share the same class
        if not isinstance(value, HashedKey):
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

    def __setstate__(self, state: RawCacheKey) -> None:
        """Restore the object state during unpickling.

        This method reconstructs the internal immutable tuple representation
        from the serialized state. Any cached hash value is intentionally
        not restored, ensuring that the hash is recomputed lazily after
        unpickling if needed.

        Args:
            state (RawCacheKey):
                The previously serialized tuple representing the cache key.
                This contains only the semantic argument structure and does
                not include any runtime-cached values such as the hash.

        """
        # Restores internal tuple only
        self.__tuple = state
