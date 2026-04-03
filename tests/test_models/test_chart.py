"""Model validation tests for chart and snapshot models."""

from importlib import import_module
from typing import Any

_models = import_module("volumeleaders.models")
Company = _models.Company
PriceBar = _models.PriceBar
Snapshot = _models.Snapshot


def test_company_model_validates_real_company_response(
    sample_company_response: dict[str, Any],
) -> None:
    """Validate Company model from real GetCompany payload."""
    company = Company.model_validate(sample_company_response)

    assert company.ticker == "SPY"
    assert "S&P 500" in company.name


def test_snapshot_model_validates_real_snapshot_response(
    sample_snapshot_response: dict[str, Any],
) -> None:
    """Validate Snapshot model from real GetSnapshot payload."""
    snapshot = Snapshot.model_validate(sample_snapshot_response["ticker"])

    assert snapshot.ticker == "SPY"
    assert snapshot.todays_change > 0


def test_price_bar_model_validates_real_price_bar_response(
    sample_price_bar_response: list[Any],
) -> None:
    """Validate PriceBar model from real chart OHLCV payload."""
    bar = PriceBar.model_validate(sample_price_bar_response[0][0])

    assert bar.open_price > 0
    assert bar.high_price > 0
    assert bar.low_price > 0
    assert bar.close_price > 0
    assert bar.volume > 0
