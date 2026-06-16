"""T031: Pydantic v2 schema validation edge cases."""

import pytest
from decimal import Decimal
from datetime import date

from pydantic import ValidationError

from app.schemas.contracts import ContractCreate, ContractUpdate, ContractFilterParams
from app.models.contracts import ContractStatus


def test_create_missing_required_fields():
    with pytest.raises(ValidationError) as exc:
        ContractCreate(value=1000, start_date=date(2026, 1, 1))
    errors = {e["loc"][0] for e in exc.value.errors()}
    assert "end_date" in errors
    assert "account_id" in errors


def test_create_end_date_before_start_date():
    with pytest.raises(ValidationError):
        ContractCreate(
            value=Decimal("5000.00"),
            start_date=date(2026, 12, 31),
            end_date=date(2026, 1, 1),
            account_id=1,
        )


def test_create_same_start_end_date_allowed():
    c = ContractCreate(
        value=Decimal("100.00"),
        start_date=date(2026, 6, 1),
        end_date=date(2026, 6, 1),
        account_id=1,
    )
    assert c.start_date == c.end_date


def test_create_negative_value_rejected():
    with pytest.raises(ValidationError):
        ContractCreate(
            value=Decimal("-1.00"),
            start_date=date(2026, 1, 1),
            end_date=date(2026, 12, 31),
            account_id=1,
        )


def test_create_value_precision_two_decimal_places():
    c = ContractCreate(
        value=Decimal("9999.99"),
        start_date=date(2026, 1, 1),
        end_date=date(2026, 12, 31),
        account_id=1,
    )
    assert c.value == Decimal("9999.99")


def test_update_dates_consistency():
    with pytest.raises(ValidationError):
        ContractUpdate(
            start_date=date(2026, 12, 31),
            end_date=date(2026, 1, 1),
        )


def test_filter_params_date_range_invalid():
    with pytest.raises(ValidationError):
        ContractFilterParams(
            end_date_from=date(2026, 12, 31),
            end_date_to=date(2026, 1, 1),
        )


def test_filter_params_defaults():
    f = ContractFilterParams()
    assert f.page == 1
    assert f.limit == 20


def test_filter_params_limit_max():
    with pytest.raises(ValidationError):
        ContractFilterParams(limit=101)
