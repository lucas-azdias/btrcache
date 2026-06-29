# Copyright (C) 2026 Lucas Dias

"""`src.btrcache.keys` unit test file."""

import pickle  # noqa: S403

import pytest

from src.btrcache.keys import HashedCacheKey

# =============================================================================
# `HashedCacheKey.__hashkey`
# =============================================================================


def test_hashkey_empty_keys_are_equal() -> None:
    assert HashedCacheKey((), {}) == HashedCacheKey((), {})


def test_hashkey_equal_positional_arguments() -> None:
    assert HashedCacheKey((1, 2, 3), {}) == HashedCacheKey((1, 2, 3), {})


def test_hashkey_equal_keys_have_equal_hashes() -> None:
    assert hash(HashedCacheKey((1, 2, 3), {})) == hash(HashedCacheKey((1, 2, 3), {}))


def test_hashkey_includes_keyword_arguments() -> None:
    assert HashedCacheKey((1, 2), {"x": 3}) == HashedCacheKey((1, 2), {"x": 3})


def test_hashkey_keyword_arguments_have_equal_hashes() -> None:
    assert hash(HashedCacheKey((1, 2), {"x": 3})) == hash(HashedCacheKey((1, 2), {"x": 3}))


def test_hashkey_distinguishes_argument_order() -> None:
    assert HashedCacheKey((1, 2, 3), {}) != HashedCacheKey((3, 2, 1), {})


def test_hashkey_distinguishes_missing_keyword_arguments() -> None:
    assert HashedCacheKey((1, 2, 3), {}) != HashedCacheKey((1, 2, 3), {"x": None})


def test_hashkey_distinguishes_keyword_values() -> None:
    assert HashedCacheKey((1, 2), {"x": 0}) != HashedCacheKey((1, 2), {"x": None})


def test_hashkey_distinguishes_keyword_names() -> None:
    assert HashedCacheKey((1, 2), {"x": 0}) != HashedCacheKey((1, 2), {"y": 0})


def test_hashkey_unhashable_argument_raises_type_error() -> None:
    with pytest.raises(TypeError):
        hash(HashedCacheKey(({},), {}))


def test_hashkey_numeric_values_compare_equal() -> None:
    assert HashedCacheKey((1, 2, 3), {}) == HashedCacheKey((1.0, 2.0, 3.0), {})


def test_hashkey_numeric_values_have_equal_hashes() -> None:
    assert hash(HashedCacheKey((1, 2, 3), {})) == hash(HashedCacheKey((1.0, 2.0, 3.0), {}))


def test_hashkey_is_hashed_cache_key_instance() -> None:
    assert isinstance(HashedCacheKey((), {}, is_typed=True), HashedCacheKey)


# =============================================================================
# `HashedCacheKey.__typed_hashkey`
# =============================================================================


def test_typed_hashkey_empty_keys_are_equal() -> None:
    assert HashedCacheKey((), {}, is_typed=True) == HashedCacheKey((), {}, is_typed=True)


def test_typed_hashkey_equal_positional_arguments() -> None:
    assert HashedCacheKey((1, 2, 3), {}, is_typed=True) == HashedCacheKey(
        (1, 2, 3),
        {},
        is_typed=True,
    )


def test_typed_hashkey_equal_keys_have_equal_hashes() -> None:
    assert hash(HashedCacheKey((1, 2, 3), {}, is_typed=True)) == hash(
        HashedCacheKey((1, 2, 3), {}, is_typed=True),
    )


def test_typed_hashkey_includes_keyword_arguments() -> None:
    assert HashedCacheKey((1, 2), {"x": 3}, is_typed=True) == HashedCacheKey(
        (1, 2),
        {"x": 3},
        is_typed=True,
    )


def test_typed_hashkey_keyword_arguments_have_equal_hashes() -> None:
    assert hash(HashedCacheKey((1, 2), {"x": 3}, is_typed=True)) == hash(
        HashedCacheKey((1, 2), {"x": 3}, is_typed=True),
    )


def test_typed_hashkey_distinguishes_argument_order() -> None:
    assert HashedCacheKey((1, 2, 3), {}, is_typed=True) != HashedCacheKey(
        (3, 2, 1),
        {},
        is_typed=True,
    )


def test_typed_hashkey_distinguishes_missing_keyword_arguments() -> None:
    assert HashedCacheKey((1, 2, 3), {}, is_typed=True) != HashedCacheKey(
        (1, 2, 3),
        {"x": None},
        is_typed=True,
    )


def test_typed_hashkey_distinguishes_keyword_values() -> None:
    assert HashedCacheKey((1, 2), {"x": 0}, is_typed=True) != HashedCacheKey(
        (1, 2),
        {"x": None},
        is_typed=True,
    )


def test_typed_hashkey_distinguishes_keyword_names() -> None:
    assert HashedCacheKey((1, 2), {"x": 0}, is_typed=True) != HashedCacheKey(
        (1, 2),
        {"y": 0},
        is_typed=True,
    )


def test_typed_hashkey_unhashable_argument_raises_type_error() -> None:
    with pytest.raises(TypeError):
        hash(HashedCacheKey(({},), {}, is_typed=True))


def test_typed_hashkey_numeric_types_compare_differently() -> None:
    assert HashedCacheKey((1, 2, 3), {}, is_typed=True) != HashedCacheKey(
        (1.0, 2.0, 3.0),
        {},
        is_typed=True,
    )


def test_typed_hashkey_is_hashed_cache_key_instance() -> None:
    assert isinstance(HashedCacheKey((), {}, is_typed=True), HashedCacheKey)


# =============================================================================
# Pickling
# =============================================================================


def test_pickle_getstate_returns_tuple() -> None:
    key = HashedCacheKey((1, 2, 3), {"a": 10, "b": 20})

    state = key.__getstate__()
    assert isinstance(state, tuple)


def test_pickle_hash_is_cached_after_first_call() -> None:
    key = HashedCacheKey((1, 2, 3), {"a": 10, "b": 20})
    _ = hash(key)

    assert hasattr(key, "_HashedCacheKey__hashvalue")


def test_pickle_does_not_store_cached_hash() -> None:
    key = HashedCacheKey((1, 2, 3), {"a": 10, "b": 20})

    _ = hash(key)
    assert hasattr(key, "_HashedCacheKey__hashvalue")

    loaded = pickle.loads(pickle.dumps(key))  # noqa: S301
    assert not hasattr(loaded, "_HashedCacheKey__hashvalue")


def test_pickle_equality_preserved_after_unpickle() -> None:
    key1 = HashedCacheKey((1, 2, 3), {"a": 10, "b": 20})
    key2 = pickle.loads(pickle.dumps(key1))  # noqa: S301

    assert key1 == key2


def test_pickle_hash_consistency_after_unpickle() -> None:
    key1 = HashedCacheKey((1, 2, 3), {"a": 10, "b": 20})
    h1 = hash(key1)

    key2 = pickle.loads(pickle.dumps(key1))  # noqa: S301
    h2 = hash(key2)

    assert h1 == h2
