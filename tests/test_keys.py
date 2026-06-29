# Copyright (C) 2026 Lucas Dias

"""`src.btrcache.keys` unit test file."""

import pickle  # noqa: S403

import pytest

from src.btrcache.keys import HashedKey, KeyHashTypedStrategy

# =============================================================================
# `HashedCacheKey.__hashkey`
# =============================================================================


def test_hashkey_empty_keys_are_equal() -> None:
    assert HashedKey((), {}) == HashedKey((), {})


def test_hashkey_equal_positional_arguments() -> None:
    assert HashedKey((1, 2, 3), {}) == HashedKey((1, 2, 3), {})


def test_hashkey_equal_keys_have_equal_hashes() -> None:
    assert hash(HashedKey((1, 2, 3), {})) == hash(HashedKey((1, 2, 3), {}))


def test_hashkey_includes_keyword_arguments() -> None:
    assert HashedKey((1, 2), {"x": 3}) == HashedKey((1, 2), {"x": 3})


def test_hashkey_keyword_arguments_have_equal_hashes() -> None:
    assert hash(HashedKey((1, 2), {"x": 3})) == hash(HashedKey((1, 2), {"x": 3}))


def test_hashkey_distinguishes_argument_order() -> None:
    assert HashedKey((1, 2, 3), {}) != HashedKey((3, 2, 1), {})


def test_hashkey_distinguishes_missing_keyword_arguments() -> None:
    assert HashedKey((1, 2, 3), {}) != HashedKey((1, 2, 3), {"x": None})


def test_hashkey_distinguishes_keyword_values() -> None:
    assert HashedKey((1, 2), {"x": 0}) != HashedKey((1, 2), {"x": None})


def test_hashkey_distinguishes_keyword_names() -> None:
    assert HashedKey((1, 2), {"x": 0}) != HashedKey((1, 2), {"y": 0})


def test_hashkey_unhashable_argument_raises_type_error() -> None:
    with pytest.raises(TypeError):
        hash(HashedKey(({},), {}))


def test_hashkey_numeric_values_compare_equal() -> None:
    assert HashedKey((1, 2, 3), {}) == HashedKey((1.0, 2.0, 3.0), {})


def test_hashkey_numeric_values_have_equal_hashes() -> None:
    assert hash(HashedKey((1, 2, 3), {})) == hash(HashedKey((1.0, 2.0, 3.0), {}))


def test_hashkey_is_hashed_cache_key_instance() -> None:
    assert isinstance(HashedKey((), {}), HashedKey)


# =============================================================================
# `HashedCacheKey.__typed_hashkey`
# =============================================================================


def test_typed_hashkey_empty_keys_are_equal() -> None:
    assert HashedKey((), {}, hash_strategy=KeyHashTypedStrategy) == HashedKey(
        (),
        {},
        hash_strategy=KeyHashTypedStrategy,
    )


def test_typed_hashkey_equal_positional_arguments() -> None:
    assert HashedKey((1, 2, 3), {}, hash_strategy=KeyHashTypedStrategy) == HashedKey(
        (1, 2, 3),
        {},
        hash_strategy=KeyHashTypedStrategy,
    )


def test_typed_hashkey_equal_keys_have_equal_hashes() -> None:
    assert hash(HashedKey((1, 2, 3), {}, hash_strategy=KeyHashTypedStrategy)) == hash(
        HashedKey((1, 2, 3), {}, hash_strategy=KeyHashTypedStrategy),
    )


def test_typed_hashkey_includes_keyword_arguments() -> None:
    assert HashedKey((1, 2), {"x": 3}, hash_strategy=KeyHashTypedStrategy) == HashedKey(
        (1, 2),
        {"x": 3},
        hash_strategy=KeyHashTypedStrategy,
    )


def test_typed_hashkey_keyword_arguments_have_equal_hashes() -> None:
    assert hash(HashedKey((1, 2), {"x": 3}, hash_strategy=KeyHashTypedStrategy)) == hash(
        HashedKey((1, 2), {"x": 3}, hash_strategy=KeyHashTypedStrategy),
    )


def test_typed_hashkey_distinguishes_argument_order() -> None:
    assert HashedKey((1, 2, 3), {}, hash_strategy=KeyHashTypedStrategy) != HashedKey(
        (3, 2, 1),
        {},
        hash_strategy=KeyHashTypedStrategy,
    )


def test_typed_hashkey_distinguishes_missing_keyword_arguments() -> None:
    assert HashedKey((1, 2, 3), {}, hash_strategy=KeyHashTypedStrategy) != HashedKey(
        (1, 2, 3),
        {"x": None},
        hash_strategy=KeyHashTypedStrategy,
    )


def test_typed_hashkey_distinguishes_keyword_values() -> None:
    assert HashedKey((1, 2), {"x": 0}, hash_strategy=KeyHashTypedStrategy) != HashedKey(
        (1, 2),
        {"x": None},
        hash_strategy=KeyHashTypedStrategy,
    )


def test_typed_hashkey_distinguishes_keyword_names() -> None:
    assert HashedKey((1, 2), {"x": 0}, hash_strategy=KeyHashTypedStrategy) != HashedKey(
        (1, 2),
        {"y": 0},
        hash_strategy=KeyHashTypedStrategy,
    )


def test_typed_hashkey_unhashable_argument_raises_type_error() -> None:
    with pytest.raises(TypeError):
        hash(HashedKey(({},), {}, hash_strategy=KeyHashTypedStrategy))


def test_typed_hashkey_numeric_types_compare_differently() -> None:
    assert HashedKey((1, 2, 3), {}, hash_strategy=KeyHashTypedStrategy) != HashedKey(
        (1.0, 2.0, 3.0),
        {},
        hash_strategy=KeyHashTypedStrategy,
    )


def test_typed_hashkey_is_hashed_cache_key_instance() -> None:
    assert isinstance(HashedKey((), {}, hash_strategy=KeyHashTypedStrategy), HashedKey)


# =============================================================================
# Pickling
# =============================================================================


def test_pickle_getstate_returns_tuple() -> None:
    key = HashedKey((1, 2, 3), {"a": 10, "b": 20})

    state = key.__getstate__()
    assert isinstance(state, tuple)


def test_pickle_hash_is_cached_after_first_call() -> None:
    key = HashedKey((1, 2, 3), {"a": 10, "b": 20})
    _ = hash(key)

    assert hasattr(key, "_HashedKey__hashvalue")


def test_pickle_does_not_store_cached_hash() -> None:
    key = HashedKey((1, 2, 3), {"a": 10, "b": 20})

    _ = hash(key)
    assert hasattr(key, "_HashedKey__hashvalue")

    loaded = pickle.loads(pickle.dumps(key))  # noqa: S301
    assert not hasattr(loaded, "_HashedKey__hashvalue")


def test_pickle_equality_preserved_after_unpickle() -> None:
    key1 = HashedKey((1, 2, 3), {"a": 10, "b": 20})
    key2 = pickle.loads(pickle.dumps(key1))  # noqa: S301

    assert key1 == key2


def test_pickle_hash_consistency_after_unpickle() -> None:
    key1 = HashedKey((1, 2, 3), {"a": 10, "b": 20})
    h1 = hash(key1)

    key2 = pickle.loads(pickle.dumps(key1))  # noqa: S301
    h2 = hash(key2)

    assert h1 == h2
