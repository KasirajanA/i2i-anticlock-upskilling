from __future__ import annotations

import asyncio

import bcrypt

from app.core.config import settings

_DUMMY_HASH = bcrypt.hashpw(b"_dummy_", bcrypt.gensalt(rounds=4)).decode()


class PasswordHasher:
    def __init__(self, rounds: int | None = None) -> None:
        self._rounds = rounds if rounds is not None else settings.bcrypt_rounds

    async def hash(self, password: str) -> str:
        loop = asyncio.get_event_loop()
        pw_bytes = password.encode()
        return await loop.run_in_executor(
            None,
            lambda: bcrypt.hashpw(pw_bytes, bcrypt.gensalt(rounds=self._rounds)).decode(),
        )

    async def verify(self, password: str, hashed: str) -> bool:
        loop = asyncio.get_event_loop()
        pw_bytes = password.encode()
        hash_bytes = hashed.encode()
        try:
            return await loop.run_in_executor(
                None, lambda: bcrypt.checkpw(pw_bytes, hash_bytes)
            )
        except Exception:
            return False

    async def dummy_verify(self) -> None:
        """Run a bcrypt verify to equalise timing when the user is not found."""
        await self.verify("_dummy_password_", _DUMMY_HASH)
