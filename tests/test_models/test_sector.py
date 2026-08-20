"""Model validation tests for sector payloads."""

from importlib import import_module
from typing import Any

_models = import_module("volumeleaders.models")
InstitutionalOutlier = _models.InstitutionalOutlier
SectorBreakdown = _models.SectorBreakdown
SectorDailyReturn = _models.SectorDailyReturn
SectorThemeNotional = _models.SectorThemeNotional
SupplyDemandArea = _models.SupplyDemandArea

_MIN_DATE_KEY = 20_000_000
_EXPECTED_RANK = 4


def test_sector_breakdown_model(
    sample_sector_breakdown_response: list[dict[str, Any]],
) -> None:
    """Validate SectorBreakdown model parses real response rows."""
    assert len(sample_sector_breakdown_response) > 0
    row = SectorBreakdown.model_validate(sample_sector_breakdown_response[0])
    assert row.date_key > _MIN_DATE_KEY
    assert isinstance(row.sector, str)
    assert row.dollars > 0


def test_institutional_outlier_model(
    sample_institutional_outliers_response: list[dict[str, Any]],
) -> None:
    """Validate InstitutionalOutlier model parses real response rows."""
    assert len(sample_institutional_outliers_response) > 0
    row = InstitutionalOutlier.model_validate(sample_institutional_outliers_response[0])
    assert row.ticker == "VCIT"
    assert row.sector == "Bonds"
    assert row.trade_rank == _EXPECTED_RANK
    assert row.sigmas > 0
    assert row.dollars > 0
    assert row.date is not None


def test_sector_theme_notional_model(
    sample_sector_themes_response: list[dict[str, Any]],
) -> None:
    """Validate SectorThemeNotional model parses real response rows."""
    assert len(sample_sector_themes_response) > 0
    row = SectorThemeNotional.model_validate(sample_sector_themes_response[0])
    assert row.sector == "Technology"
    assert row.theme_slug == "enterprise-software"
    assert row.ticker == "AAPL"
    assert row.theme_pct_of_sector > 0
    assert row.ticker_pct_of_theme > 0
    assert row.dollars > 0


def test_supply_demand_area_model(
    sample_supply_demand_areas_response: list[dict[str, Any]],
) -> None:
    """Validate SupplyDemandArea model parses real response rows."""
    assert len(sample_supply_demand_areas_response) > 0
    row = SupplyDemandArea.model_validate(sample_supply_demand_areas_response[0])
    assert row.sector == "Communication Services"
    assert row.ticker_count > 0
    assert row.median_pct_levels_below_latest_close >= 0


def test_sector_daily_return_model(
    sample_sector_daily_returns_response: list[dict[str, Any]],
) -> None:
    """Validate SectorDailyReturn model parses real response rows."""
    assert len(sample_sector_daily_returns_response) > 0
    row = SectorDailyReturn.model_validate(sample_sector_daily_returns_response[0])
    assert row.sector == "Bonds"
    assert row.date is not None
    assert row.ticker_count > 0
    assert row.spy_close > 0
