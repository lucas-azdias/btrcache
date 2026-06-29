# Copyright (C) 2026 Lucas Dias
#
# Portions Copyright (C) 2026 James Ward
# Source: https://github.com/imnotjames/cachetools-async/blob/53d453441dac736b16ec549ee4dd50453c9669c9/src/cachetools_async/decorators.py
# License: MIT (See LICENSE file for details)

"""Asynchronous caching utilities for coroutines and methods.

This module provides async-compatible decorator patterns similar to
`cachetools`, designed to store and reuse `Future` instances to prevent
duplicate in-flight executions (cache stampede) and cache completed
results.
"""

import asyncio
import contextlib
import functools
import inspect
import typing

from src.btrcache.keys import HashedKey, KeyHashStrategy, KeyHashStrategyProtocol

if typing.TYPE_CHECKING:
    import collections.abc

    from src.btrcache.asyncio.cache import AsyncCache

__all__: typing.Final = ("async_cached", "async_cachedmethod")


def __async_cache_get[R](
    *,
    cache: AsyncCache[R],
    key: HashedKey,
    call_fn: collections.abc.Callable[[], collections.abc.Coroutine[typing.Any, typing.Any, R]],
    result_predicate: collections.abc.Callable[[typing.Any], bool] = lambda _: True,
    exception_predicate: collections.abc.Callable[[BaseException], bool] = lambda _: True,
) -> tuple[asyncio.Task[R], asyncio.Future[R]]:
    with contextlib.suppress(KeyError):
        # If alrady exists a cached version, return it
        return cache[key]

    # Creates a new task for this call
    loop = asyncio.get_event_loop()
    task = loop.create_task(call_fn())
    future: asyncio.Future[R] = loop.create_future()

    # `done` callback for when future is concluded
    def done(t: asyncio.Task[R]) -> None:
        # Removes cancelled tasks from the cache
        if t.cancelled():
            cache.pop(key, None)
            future.cancel()
            return

        # Treats thrown exceptions inside executed task
        exception = t.exception()
        if exception is not None:
            # Validates if the thrown exception should invalidate caching
            if not exception_predicate(exception):
                cache.pop(key, None)

            # Propagates the exception
            future.set_exception(exception)
            return

        # Successful result
        result = t.result()

        # Validates if the result should invalidate caching
        if not result_predicate(result):
            cache.pop(key, None)

        # Stores the successful result in the shared future
        future.set_result(result)

    # Adds `done` callback of future to task
    task.add_done_callback(done)

    # Returns the cached value
    with contextlib.suppress(ValueError):
        cache[key] = (task, future)

    return task, future


class __AsyncCachedFunctionWrapperProtocol[**P, R](typing.Protocol):
    """Protocol for cached asynchronous function wrappers."""

    cache: AsyncCache[R] | None
    cache_key: KeyHashStrategyProtocol
    cache_lock: contextlib.AbstractContextManager[typing.Any] | None
    cache_info: bool | None
    cache_clear: collections.abc.Callable[[], None]

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> collections.abc.Awaitable[R]:
        raise NotImplementedError


class __AsyncCachedMethodWrapperProtocol[**P, R](typing.Protocol):
    """Protocol for cached asynchronous method wrappers."""

    cache: collections.abc.Callable[[typing.Any], AsyncCache[R] | None]
    cache_key: KeyHashStrategyProtocol
    cache_lock: contextlib.AbstractContextManager[typing.Any] | None
    cache_info: bool | None
    cache_clear: collections.abc.Callable[[typing.Any], None]

    def __call__(self, *args: P.args, **kwargs: P.kwargs) -> collections.abc.Awaitable[R]:
        raise NotImplementedError

    def __get__(
        self,
        # IGNORE: Type `Any` was used as it must The descriptor
        # is accessed from an instance of the class containing
        # the decorated method which must be any arbitrary
        # user-defined type.
        instance: typing.Any,  # noqa: ANN401
        owner: type | None,
    ) -> __AsyncCachedMethodWrapperProtocol[P, R]:
        if instance is None:
            return self

        # Binds the method to the instance at runtime
        bound = typing.cast(
            "__AsyncCachedMethodWrapperProtocol[P, R]",
            functools.partial(self.__call__, instance),
        )

        # Mirrors the cache attributes to the bound wrapper
        bound.cache = self.cache
        bound.cache_key = self.cache_key
        bound.cache_lock = self.cache_lock
        bound.cache_info = self.cache_info
        bound.cache_clear = self.cache_clear

        return bound


class __AsyncFunctionDecoratorProtocol(typing.Protocol):
    """Protocol representing a decorator that wraps an async function."""

    def __call__[**P, R](
        self,
        fn: collections.abc.Callable[P, collections.abc.Awaitable[R]],
    ) -> __AsyncCachedFunctionWrapperProtocol[P, R]:
        raise NotImplementedError


class __AsyncMethodDecoratorProtocol(typing.Protocol):
    """Protocol representing a decorator that wraps an async instance method."""

    def __call__[SelfT, **P, R](
        self,
        fn: collections.abc.Callable[typing.Concatenate[SelfT, P], collections.abc.Awaitable[R]],
    ) -> __AsyncCachedMethodWrapperProtocol[P, R]:
        raise NotImplementedError


# IGNORE: Function defines a public interface
# that necessitates many arguments
def async_cached(  # noqa: PLR0913
    cache: AsyncCache[typing.Any] | None,
    *,
    key_hash_strategy: KeyHashStrategyProtocol = KeyHashStrategy,
    lock: contextlib.AbstractContextManager[typing.Any] | None = None,
    info: bool = False,
    result_predicate: collections.abc.Callable[[typing.Any], bool] = lambda _: True,
    exception_predicate: collections.abc.Callable[[BaseException], bool] = lambda _: True,
) -> __AsyncFunctionDecoratorProtocol:
    """Decorate caching async function results using asyncio `Future`.

    This decorator stores `Future` objects in a shared mapping keyed by
    deterministic `HashedKey` objects generated from the supplied
    `key_hash_strategy`. It ensures that concurrent callers awaiting the
    same computation will reuse the same in-progress `Future`, preventing
    duplicate execution (cache stampede protection).

    Args:
        cache (AsyncCache[Any] | None):
            Cache used to store tasks and futures. If None, caching is disabled.

        key_hash_strategy (KeyHashStrategyProtocol):
            Strategy used to compute deterministic cache keys from the
            positional and keyword arguments. Defaults to `KeyHashStrategy`.

        lock (AbstractContextManager[Any] | None):
            Optional lock context manager. Not supported in this implementation.

        info (bool):
            If True, raises NotImplementedError (not supported).

        result_predicate (Callable[[Any], bool]):
            A custom callable that receives the completed result of the
            coroutine and returns True if it should remain cached. If it
            returns False, the result is evicted from the cache immediately
            upon completion. Defaults to a lambda that always returns True.

        exception_predicate (Callable[[BaseException], bool]):
            A custom callable that receives the raised exception if the
            coroutine fails, returning True if the exception should be cached.
            If it returns False, the failed future is evicted, allowing
            subsequent calls to retry execution. Defaults to a lambda that
            always returns True.

    Returns:
        __AsyncFunctionDecoratorProtocol:
            A decorator that wraps an async function with caching behavior.

    Raises:
        NotImplementedError:
            If `info` or `lock` are provided.

    """
    if info:
        msg = "`info` is not supported"
        raise NotImplementedError(msg)

    if lock is not None:
        msg = "`lock` is not supported"
        raise NotImplementedError(msg)

    def decorator[**P, R](
        fn: collections.abc.Callable[P, collections.abc.Awaitable[R]],
    ) -> __AsyncCachedFunctionWrapperProtocol[P, R]:
        if not inspect.iscoroutinefunction(fn):
            msg = f"Expected 'Coroutine' function, got {fn}"
            raise TypeError(msg)

        async def wrapper(*args: P.args, **kwargs: P.kwargs) -> R:
            if cache is None:
                return await fn(*args, **kwargs)

            # Generates key
            generated_key = HashedKey(args, kwargs, hash_strategy=key_hash_strategy)

            task, future = __async_cache_get(
                cache=cache,
                key=generated_key,
                call_fn=lambda: fn(*args, **kwargs),
                result_predicate=result_predicate,
                exception_predicate=exception_predicate,
            )

            try:
                return await future
            except asyncio.CancelledError:
                # If an awaiting caller is cancelled, the corresponding cache entry is
                # removed and the underlying task is cancelled when appropriate

                # Evicts from cache instantly
                cache.pop(generated_key, None)

                # Directly terminates the underlying task loop execution
                if not task.done():
                    task.cancel()

                raise

        wrapped = typing.cast(
            "__AsyncCachedFunctionWrapperProtocol[P, R]",
            functools.update_wrapper(wrapper, fn),
        )

        wrapped.cache = cache
        wrapped.cache_key = key_hash_strategy
        wrapped.cache_lock = None
        wrapped.cache_info = None
        wrapped.cache_clear = lambda: cache.clear() if cache is not None else None

        return wrapped

    return decorator


# IGNORE: Function defines a public interface
# that necessitates many arguments
def async_cachedmethod(  # noqa: PLR0913
    cache: collections.abc.Callable[[typing.Any], AsyncCache[typing.Any] | None],
    *,
    key_hash_strategy: KeyHashStrategyProtocol = KeyHashStrategy,
    lock: collections.abc.Callable[[typing.Any], contextlib.AbstractContextManager[typing.Any]]
    | None = None,
    info: bool = False,
    result_predicate: collections.abc.Callable[[typing.Any], bool] = lambda _: True,
    exception_predicate: collections.abc.Callable[[BaseException], bool] = lambda _: True,
) -> __AsyncMethodDecoratorProtocol:
    """Decorate caching async instance/class methods.

    This is similar to `cached`, but the cache is resolved dynamically
    per instance (or class) via the provided cache function.

    It is primarily used for memoizing async methods where cache storage
    is attached to `self` or another runtime context.

    Args:
        cache (Callable[[Any], AsyncCache[Any] | None]):
            Callable that returns an `AsyncCache` for the given instance,
            or None to disable caching for that instance.

        key_hash_strategy (KeyHashStrategyProtocol):
            Strategy used to compute deterministic cache keys from the
            positional and keyword arguments. Defaults to `KeyHashStrategy`.

        lock (Callable[[Any], AbstractContextManager[Any]] | None):
            Optional lock context manager factory. Not supported.

        info (bool):
            If True, raises NotImplementedError (not supported).

        result_predicate (Callable[[Any], bool]):
            A custom callable that receives the completed result of the
            coroutine and returns True if it should remain cached. If it
            returns False, the result is evicted from the cache immediately
            upon completion. Defaults to a lambda that always returns True.

        exception_predicate (Callable[[BaseException], bool]):
            A custom callable that receives the raised exception if the
            coroutine fails, returning True if the exception should be cached.
            If it returns False, the failed future is evicted, allowing
            subsequent calls to retry execution. Defaults to a lambda that
            always returns True.

    Returns:
        __AsyncMethodDecoratorProtocol:
            A decorator that wraps an async method with caching behavior.

    Raises:
        NotImplementedError:
            If `info` or `lock` are provided.

    """
    if info:
        msg = "`info` is not supported"
        raise NotImplementedError(msg)

    if lock is not None:
        msg = "`lock` is not supported"
        raise NotImplementedError(msg)

    def decorator[SelfT, **P, R](
        fn: collections.abc.Callable[typing.Concatenate[SelfT, P], collections.abc.Awaitable[R]],
    ) -> __AsyncCachedMethodWrapperProtocol[P, R]:
        if not inspect.iscoroutinefunction(fn):
            msg = f"Expected 'Coroutine' function, got {fn}"
            raise TypeError(msg)

        async def wrapper(self_obj: SelfT, *args: P.args, **kwargs: P.kwargs) -> R:
            self_cache = cache(self_obj)

            if self_cache is None:
                return await fn(self_obj, *args, **kwargs)

            # Generates key
            generated_key = HashedKey(args, kwargs, hash_strategy=key_hash_strategy)

            task, future = __async_cache_get(
                cache=self_cache,
                key=generated_key,
                call_fn=lambda: fn(self_obj, *args, **kwargs),
                result_predicate=result_predicate,
                exception_predicate=exception_predicate,
            )

            try:
                return await future
            except asyncio.CancelledError:
                # If an awaiting caller is cancelled, the corresponding cache entry is
                # removed and the underlying task is cancelled when appropriate

                # Evicts from cache instantly
                self_cache.pop(generated_key, None)

                # Directly terminates the underlying task loop execution
                if not task.done():
                    task.cancel()

                raise

        wrapped = typing.cast(
            "__AsyncCachedMethodWrapperProtocol[P, R]",
            functools.update_wrapper(wrapper, fn),
        )

        wrapped.cache = cache
        wrapped.cache_key = key_hash_strategy
        wrapped.cache_lock = None
        wrapped.cache_info = None
        wrapped.cache_clear = lambda self_obj: (
            self_cache.clear() if (self_cache := cache(self_obj)) is not None else None
        )

        return wrapped

    return decorator
