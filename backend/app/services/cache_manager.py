from __future__ import annotations

import asyncio
import hashlib
import json
from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from cachetools import TTLCache


@dataclass(frozen=True)
class ReportCacheKey:
    report_type: str
    role: str
    owner_id: int | None
    filters_hash: str
    version: int

    @staticmethod
    def make(report_type: str, role: str, owner_id: int | None, filters: dict[str, Any], version: int) -> "ReportCacheKey":
        filters_hash = hashlib.sha256(
            json.dumps(filters, sort_keys=True, default=str).encode()
        ).hexdigest()[:16]
        return ReportCacheKey(
            report_type=report_type,
            role=role,
            owner_id=owner_id,
            filters_hash=filters_hash,
            version=version,
        )


class CacheInvalidator:
    def __init__(self) -> None:
        self._versions: dict[str, int] = {}

    def invalidate(self, report_type: str) -> None:
        self._versions[report_type] = self._versions.get(report_type, 0) + 1

    def version(self, report_type: str) -> int:
        return self._versions.get(report_type, 0)


class CacheManager:
    _caches: dict[str, TTLCache] = {
        "support": TTLCache(maxsize=256, ttl=60),
        "default": TTLCache(maxsize=1024, ttl=300),
    }
    _lock = asyncio.Lock()
    invalidator = CacheInvalidator()

    async def get_or_set(
        self,
        key: ReportCacheKey,
        factory: Callable[[], Awaitable[Any]],
    ) -> Any:
        cache = self._caches.get(key.report_type, self._caches["default"])
        async with self._lock:
            if key in cache:
                return cache[key]
            result = await factory()
            cache[key] = result
            return result
