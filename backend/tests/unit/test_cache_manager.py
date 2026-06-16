"""Unit tests for CacheManager."""

import asyncio

import pytest

from app.services.cache_manager import CacheManager, ReportCacheKey


def _key(report_type: str = "sales", filters: dict | None = None, version: int = 0) -> ReportCacheKey:
    return ReportCacheKey.make(
        report_type=report_type,
        role="Admin",
        owner_id=None,
        filters=filters or {},
        version=version,
    )


@pytest.mark.asyncio
async def test_cache_returns_same_value_for_same_key():
    mgr = CacheManager()
    key = _key()
    calls = 0

    async def factory():
        nonlocal calls
        calls += 1
        return "result"

    r1 = await mgr.get_or_set(key, factory)
    r2 = await mgr.get_or_set(key, factory)
    assert r1 == r2 == "result"
    assert calls == 1


@pytest.mark.asyncio
async def test_different_filter_hash_calls_factory_twice():
    mgr = CacheManager()
    key1 = _key(filters={"owner_id": 1})
    key2 = _key(filters={"owner_id": 2})
    calls = 0

    async def factory():
        nonlocal calls
        calls += 1
        return calls

    await mgr.get_or_set(key1, factory)
    await mgr.get_or_set(key2, factory)
    assert calls == 2


@pytest.mark.asyncio
async def test_version_invalidation_causes_different_key():
    mgr = CacheManager()
    key_v0 = _key(version=0)
    key_v1 = _key(version=1)
    assert key_v0 != key_v1


@pytest.mark.asyncio
async def test_support_cache_is_separate_instance():
    """Support and default caches must be separate TTLCache instances."""
    mgr = CacheManager()
    assert mgr._caches["support"] is not mgr._caches["default"]


@pytest.mark.asyncio
async def test_concurrent_reads_return_consistent_value():
    mgr = CacheManager()
    key = _key(report_type="contract", filters={"x": 1})
    call_count = 0

    async def factory():
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0)
        return "shared"

    results = await asyncio.gather(
        mgr.get_or_set(key, factory),
        mgr.get_or_set(key, factory),
        mgr.get_or_set(key, factory),
    )
    assert all(r == "shared" for r in results)
