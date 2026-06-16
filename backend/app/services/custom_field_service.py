from __future__ import annotations

import re

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.contact import CustomFieldDefinition, CustomFieldValue

VALID_FIELD_TYPES = {"text", "number", "date", "boolean", "select"}
_KEY_PATTERN = re.compile(r"^[a-z][a-z0-9_]{2,49}$")


class CustomFieldService:
    def __init__(self, session: AsyncSession) -> None:
        self._db = session

    async def create_definition(
        self,
        entity_type: str,
        field_key: str,
        label: str,
        field_type: str,
        options: list | None,
        required: bool,
        created_by_id: int | None,
    ) -> CustomFieldDefinition:
        if not _KEY_PATTERN.match(field_key):
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="field_key must be snake_case 3–50 chars.",
            )
        if field_type not in VALID_FIELD_TYPES:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"field_type must be one of {sorted(VALID_FIELD_TYPES)}.",
            )
        if field_type == "select" and not options:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="options required when field_type=select.",
            )

        existing = (await self._db.execute(
            select(CustomFieldDefinition).where(
                CustomFieldDefinition.field_key == field_key
            )
        )).scalar_one_or_none()
        if existing:
            raise HTTPException(status.HTTP_409_CONFLICT, detail="field_key already exists.")

        defn = CustomFieldDefinition(
            entity_type=entity_type,
            field_key=field_key,
            label=label,
            field_type=field_type,
            options=options,
            required=required,
            created_by_id=created_by_id,
        )
        self._db.add(defn)
        await self._db.commit()
        await self._db.refresh(defn)
        return defn

    async def list_definitions(self, entity_type: str) -> list[CustomFieldDefinition]:
        result = await self._db.execute(
            select(CustomFieldDefinition)
            .where(CustomFieldDefinition.entity_type == entity_type)
            .order_by(CustomFieldDefinition.created_at)
        )
        return list(result.scalars().all())

    async def get_values(self, entity_type: str, entity_id: int) -> list[dict]:
        defns = await self.list_definitions(entity_type)
        result = await self._db.execute(
            select(CustomFieldValue).where(
                CustomFieldValue.entity_type == entity_type,
                CustomFieldValue.entity_id == entity_id,
            )
        )
        values_by_defn = {v.definition_id: v.field_value for v in result.scalars().all()}
        return [
            {"key": d.field_key, "label": d.label, "value": values_by_defn.get(d.id)}
            for d in defns
        ]

    async def set_value(
        self,
        definition_id: int,
        entity_type: str,
        entity_id: int,
        raw_value: str | None,
    ) -> CustomFieldValue:
        existing = (await self._db.execute(
            select(CustomFieldValue).where(
                CustomFieldValue.definition_id == definition_id,
                CustomFieldValue.entity_type == entity_type,
                CustomFieldValue.entity_id == entity_id,
            )
        )).scalar_one_or_none()

        if existing:
            existing.field_value = raw_value
            await self._db.commit()
            return existing

        cfv = CustomFieldValue(
            definition_id=definition_id,
            entity_type=entity_type,
            entity_id=entity_id,
            field_value=raw_value,
        )
        self._db.add(cfv)
        await self._db.commit()
        await self._db.refresh(cfv)
        return cfv
