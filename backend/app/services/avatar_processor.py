from __future__ import annotations

import asyncio
import io
import os

from fastapi import HTTPException, UploadFile, status

_STORAGE_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "..", "storage", "avatars")


class AvatarProcessor:
    MAX_BYTES = 2 * 1024 * 1024  # 2 MB
    OUTPUT_SIZE = (200, 200)
    ALLOWED_MIME = {"image/jpeg", "image/png", "image/webp"}

    async def process(self, upload: UploadFile, user_id: int) -> str:
        if upload.content_type not in self.ALLOWED_MIME:
            raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Unsupported image format.")
        data = await upload.read()
        if len(data) > self.MAX_BYTES:
            raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File exceeds 2 MB limit.")
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self._resize_and_save, data, user_id)
        return f"/static/avatars/{user_id}.webp"

    def _resize_and_save(self, data: bytes, user_id: int) -> str:
        from PIL import Image  # noqa: PLC0415 — lazy import to avoid top-level overhead
        img = Image.open(io.BytesIO(data)).convert("RGB")
        img = img.resize(self.OUTPUT_SIZE, Image.LANCZOS)
        os.makedirs(_STORAGE_DIR, exist_ok=True)
        dest = os.path.join(_STORAGE_DIR, f"{user_id}.webp")
        img.save(dest, format="WEBP", quality=85)
        return dest
