"""
Thread-safe caching service
"""

import threading
from typing import Any, Dict, Callable
from datetime import datetime, timedelta


class ThreadSafeCache:
    def __init__(self):
        self._store = {}
        self._lock = threading.RLock()

    def get(self, key: str):
        with self._lock:
            if key not in self._store:
                return None
            expiry, value = self._store[key]
            if datetime.now() > expiry:
                del self._store[key]
                return None
            return value

    def set(self, key: str, value: Any, ttl_seconds: int = 30):
        with self._lock:
            expiry = datetime.now() + timedelta(seconds=ttl_seconds)
            self._store[key] = (expiry, value)

    def delete(self, key: str):
        with self._lock:
            self._store.pop(key, None)

    def clear(self):
        with self._lock:
            self._store.clear()

    def get_or_compute(self, key: str, compute: Callable, ttl_seconds: int = 30):
        value = self.get(key)
        if value is not None:
            return value
        value = compute()
        self.set(key, value, ttl_seconds)
        return value


_cache_instance = None
_cache_lock = threading.Lock()


def get_cache():
    global _cache_instance
    if _cache_instance is None:
        with _cache_lock:
            if _cache_instance is None:
                _cache_instance = ThreadSafeCache()
    return _cache_instance
