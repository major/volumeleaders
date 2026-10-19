"""Behavioral tests for ASP.NET date coercion through public models."""

from datetime import UTC, datetime
from importlib import import_module
from typing import Any

import pytest

Earnings = import_module("volumeleaders.models").Earnings


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        pytest.param(None, None, id="null"),
        pytest.param("/Date(0)/", datetime(1970, 1, 1, tzinfo=UTC), id="epoch"),
        pytest.param(123, None, id="unsupported_integer"),
    ],
)
def test_earnings_model_coerces_aspnet_dates(
    sample_earnings_response: dict[str, Any],
    raw: object,
    expected: datetime | None,
) -> None:
    """Coerce API-style date values during Earnings model validation."""
    row = dict(sample_earnings_response["data"][0])
    row["EarningsDate"] = raw

    assert Earnings.model_validate(row).earnings_date == expected


def test_earnings_model_keeps_datetime_dates(
    sample_earnings_response: dict[str, Any],
) -> None:
    """Preserve datetime values supplied by callers or other models."""
    now = datetime.now(tz=UTC)
    row = dict(sample_earnings_response["data"][0])
    row["EarningsDate"] = now

    assert Earnings.model_validate(row).earnings_date == now
