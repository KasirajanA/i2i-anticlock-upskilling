"""Unit tests for PasswordHasher."""

import pytest

from app.services.password_hasher import PasswordHasher


@pytest.fixture
def hasher():
    # Use cost 4 for faster tests
    return PasswordHasher(rounds=4)


@pytest.mark.asyncio
async def test_hash_returns_bcrypt_string(hasher):
    result = await hasher.hash("password123")
    assert result.startswith("$2b$")


@pytest.mark.asyncio
async def test_verify_round_trip_succeeds(hasher):
    hashed = await hasher.hash("correct_password")
    assert await hasher.verify("correct_password", hashed) is True


@pytest.mark.asyncio
async def test_verify_wrong_password_fails(hasher):
    hashed = await hasher.hash("correct_password")
    assert await hasher.verify("wrong_password", hashed) is False


@pytest.mark.asyncio
async def test_dummy_verify_completes_without_error(hasher):
    await hasher.dummy_verify()
