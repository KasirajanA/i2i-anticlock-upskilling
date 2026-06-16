from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import Select, func, select


VALID_FIELDS = {"name", "email", "tag", "account_id", "custom_field_key"}
VALID_OPERATORS = {"eq", "contains", "in"}


class FilterQueryBuilder:
    """Builds a filtered SQLAlchemy SELECT for contacts."""

    FIELD_MAP: dict[str, str] = {
        "name": "name",
        "email": "email",
        "tag": "tag",
        "account_id": "account_id",
        "custom_field_key": "custom_field_key",
    }

    def __init__(self) -> None:
        self._conditions: list[dict] = []

    def add(self, field: str, operator: str, value) -> "FilterQueryBuilder":
        self._conditions.append({"field": field, "operator": operator, "value": value})
        return self

    def build(self, base_query: Select) -> Select:
        from app.models.contact import Contact, ContactAccount  # noqa: PLC0415

        for cond in self._conditions:
            field = cond["field"]
            op = cond["operator"]
            val = cond["value"]

            if field == "name":
                full_name = func.concat(Contact.first_name, " ", Contact.last_name)
                if op == "contains":
                    base_query = base_query.where(full_name.ilike(f"%{val}%"))
                elif op == "eq":
                    base_query = base_query.where(full_name == val)
            elif field == "email":
                if op == "contains":
                    base_query = base_query.where(Contact.email.ilike(f"%{val}%"))
                elif op == "eq":
                    base_query = base_query.where(Contact.email == val)
            elif field == "tag":
                base_query = base_query.where(Contact.tags.contains([val]))
            elif field == "account_id":
                base_query = base_query.where(
                    Contact.id.in_(
                        select(ContactAccount.contact_id).where(ContactAccount.account_id == int(val))
                    )
                )

        return base_query

    def validate_spec(self, filter_spec: dict) -> None:
        conditions = filter_spec.get("conditions", [])
        if len(conditions) > 5:
            raise HTTPException(
                status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Maximum 5 filter conditions allowed.",
            )
        for cond in conditions:
            if cond.get("field") not in VALID_FIELDS:
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Unknown filter field: {cond.get('field')}",
                )
            if cond.get("operator") not in VALID_OPERATORS:
                raise HTTPException(
                    status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail=f"Unknown operator: {cond.get('operator')}",
                )
