"""Model validation tests for earnings payloads."""

from datetime import datetime
from importlib import import_module
from typing import Any

Earnings = import_module("volumeleaders.models").Earnings


def test_earnings_model_validates_real_response(
    sample_earnings_response: dict[str, Any],
) -> None:
    """Validate Earnings model parsing, including ASP.NET date conversion."""
    row = sample_earnings_response["data"][0]
    earnings = Earnings.model_validate(row)

    assert earnings.ticker == "BSET"
    assert isinstance(earnings.earnings_date, datetime)
