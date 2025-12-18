from __future__ import annotations

from collections import OrderedDict
from typing import Optional

import hashlib


def build_cache_key(model: str, adapter: str, prompt: str) -> str:
    digest = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    return f"{model}:{adapter}:{digest}"


class LRUCache:
    def __init__(self, capacity: int) -> None:
        self.capacity = max(capacity, 1)
        self._data: "OrderedDict[str, str]" = OrderedDict()

    def get(self, key: str) -> Optional[str]:
        if key not in self._data:
            return None
        self._data.move_to_end(key)
        return self._data[key]

    def set(self, key: str, value: str) -> None:
        self._data[key] = value
        self._data.move_to_end(key)
        if len(self._data) > self.capacity:
            self._data.popitem(last=False)


class RedisCache:
    def __init__(self, url: str) -> None:
        import redis

        self._client = redis.Redis.from_url(url)

    def get(self, key: str) -> Optional[str]:
        value = self._client.get(key)
        if value is None:
            return None
        return value.decode("utf-8")

    def set(self, key: str, value: str, ttl_seconds: int = 3600) -> None:
        self._client.setex(key, ttl_seconds, value)
