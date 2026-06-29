# `btrcache`

[![Latest PyPI version](https://img.shields.io/pypi/v/btrcache)](https://pypi.org/project/btrcache/)
[![Tests workflow status](https://img.shields.io/github/actions/workflow/status/lucas-azdias/btrcache/tests.yml?label=tests)](https://github.com/tkem/cachetools/actions/workflows/tests.yml)
[![Publish workflow status](https://img.shields.io/github/actions/workflow/status/lucas-azdias/btrcache/publish.yml?label=publish)](https://github.com/tkem/cachetools/actions/workflows/publish.yml)
[![Coverage](https://img.shields.io/codecov/c/github/lucas-azdias/btrcache/main.svg)](https://codecov.io/gh/lucas-azdias/btrcache)
[![License](https://img.shields.io/github/license/lucas-azdias/btrcache)](https://raw.github.com/lucas-azdias/btrcache/master/LICENSE)

High-performance caching tools, memoization decorators, and cache collections for Python.

---

## Overview

**`btrcache`** is a Python library that provides a flexible set of in-memory caching primitives, decorators, and cache collections designed for both synchronous and asynchronous workloads.

## Installation

```bash
pip install btrcache
```

<!--
## Quick Start

### Simple function memoization

```python
from btrcache import cached

@cached()
def fib(n: int) -> int:
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)
```

### Custom cache size

```python
from btrcache import cached, LRUCache

@cached(cache_factory=lambda: LRUCache(maxsize=1024))
def compute(x):
    return x * x
```
-->

## Roadmap

* [X] Key generators
* [X] Asynchronous decorators
* [ ] Create tests
* [ ] Release in PyPi
* [ ] Synchronous decorators
* [ ] Cache collections
* [ ] Optimizations

## Contributing

Contributions are welcome. Please ensure:

* Code is type-annotated;
* Tests cover edge cases.

## Acknowledgements

This project builds upon ideas and implementations from the following open-source projects:

- [`cachetools`](https://github.com/tkem/cachetools/) - An extensible set of memoizing collections and decorators for Python. Developed and maintained by [Thomas Kemmer](https://github.com/tkem/).
- [`cachetools-async`](https://github.com/imnotjames/cachetools-async/) - Python library that extends `cachetools` with async decorators. Created by [James Ward](https://github.com/imnotjames/).

## License

Copyright (C) 2026 Lucas Dias.

Licensed under the [MIT License](LICENSE).
