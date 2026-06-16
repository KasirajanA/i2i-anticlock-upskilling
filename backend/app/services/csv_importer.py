from __future__ import annotations

import csv
import io
import re

from fastapi import UploadFile
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.sqlite_contact_repository import SqliteContactRepository
from app.schemas.contact import ImportResultResponse

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


class CSVImporter:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session
        self._repo = SqliteContactRepository(session)

    async def import_file(self, upload: UploadFile, duplicate_mode: str = "skip") -> ImportResultResponse:
        content = await upload.read()
        text = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))

        imported = 0
        skipped = 0
        errors = 0
        error_details: list[dict] = []
        batch: list[dict] = []

        for row_num, row in enumerate(reader, start=2):
            email = (row.get("email") or "").strip().lower()
            first_name = (row.get("first_name") or "").strip()
            last_name = (row.get("last_name") or "").strip()

            if not first_name or not last_name:
                errors += 1
                error_details.append({"row": row_num, "reason": "first_name and last_name required"})
                continue
            if not email or not _EMAIL_RE.match(email):
                errors += 1
                error_details.append({"row": row_num, "reason": "valid email required"})
                continue

            existing = await self._repo.find_by_email(email)
            if existing:
                if duplicate_mode == "skip":
                    skipped += 1
                    continue
                elif duplicate_mode == "overwrite":
                    await self._repo.update(existing.id, {
                        "first_name": first_name,
                        "last_name": last_name,
                        "phone": row.get("phone") or None,
                        "job_title": row.get("job_title") or None,
                    })
                    imported += 1
                    continue

            batch.append({
                "first_name": first_name,
                "last_name": last_name,
                "name": f"{first_name} {last_name}",
                "email": email,
                "phone": row.get("phone") or None,
                "job_title": row.get("job_title") or None,
                "tags": [],
            })

            if len(batch) >= 100:
                for contact_data in batch:
                    await self._repo.create(contact_data, [])
                imported += len(batch)
                batch = []

        for contact_data in batch:
            await self._repo.create(contact_data, [])
        imported += len(batch)

        return ImportResultResponse(
            imported=imported,
            skipped=skipped,
            errors=errors,
            error_details=error_details,
        )
