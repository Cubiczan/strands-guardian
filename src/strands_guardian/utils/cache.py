from __future__ import annotations

import threading
import time
from collections import OrderedDict
from typing import Any, Callable, Optional


class TimedCache:
    """Thread-safe LRU cache with per-entry TTL."""

    def __init__(self, default_ttl: float = 900.0, max_size: int = 512):
        self._store: OrderedDict[str, tuple[float, Any]] = OrderedDict()
        self._default_ttl = default_ttl
        self._max_size = max_size
        self._lock = threading.Lock()

    def get(self, key: str, ttl: Optional[float] = None) -> Optional[Any]:
        effective_ttl = ttl if ttl is not None else self._default_ttl
        with self._lock:
            if key in self._store:
                ts, val = self._store[key]
                if time.monotonic() - ts < effective_ttl:
                    self._store.move_to_end(key)
                    return val
                del self._store[key]
        return None

    def set(self, key: str, value: Any) -> None:
        with self._lock:
            if key in self._store:
                del self._store[key]
            self._store[key] = (time.monotonic(), value)
            while len(self._store) > self._max_size:
                self._store.popitem(last=False)

    def get_or_compute(
        self, key: str, fn: Callable[[], Any], ttl: Optional[float] = None
    ) -> Any:
        cached = self.get(key, ttl)
        if cached is not None:
            return cached
        result = fn()
        self.set(key, result)
        return result

    def clear(self) -> None:
        with self._lock:
            self._store.clear()

    @property
    def size(self) -> int:
        with self._lock:
            return len(self._store)
