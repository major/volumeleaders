"""Tests for sector endpoint functions."""

from importlib import import_module
from typing import Any
from unittest.mock import Mock

_endpoints = import_module("volumeleaders.endpoints.sector")
get_sector_breakdown = _endpoints.get_sector_breakdown
get_institutional_outliers = _endpoints.get_institutional_outliers
get_notional_by_sector_by_name = _endpoints.get_notional_by_sector_by_name
get_supply_demand_areas = _endpoints.get_supply_demand_areas
get_sector_daily_returns = _endpoints.get_sector_daily_returns


def test_get_sector_breakdown(
    sample_sector_breakdown_response: list[dict[str, Any]],
) -> None:
    """Validate get_sector_breakdown returns typed models."""
    client = Mock()
    client.post_json.return_value = sample_sector_breakdown_response

    results = get_sector_breakdown(
        client,
        start_date="2026-08-12",
        end_date="2026-08-19",
    )

    client.post_json.assert_called_once_with(
        "/SectorBreakdown/GetSectorBreakdown",
        {"StartDateKey": "20260812", "EndDateKey": "20260819"},
    )
    assert len(results) == len(sample_sector_breakdown_response)
    assert results[0].sector == "Bonds"


def test_get_sector_breakdown_defaults(
    sample_sector_breakdown_response: list[dict[str, Any]],
) -> None:
    """Validate get_sector_breakdown handles empty dates and date keys."""
    client = Mock()
    client.post_json.return_value = sample_sector_breakdown_response

    results = get_sector_breakdown(
        client,
        start_date="20260812",
        end_date="",
    )

    client.post_json.assert_called_once_with(
        "/SectorBreakdown/GetSectorBreakdown",
        {"StartDateKey": "20260812", "EndDateKey": ""},
    )
    assert len(results) == len(sample_sector_breakdown_response)


def test_get_institutional_outliers(
    sample_institutional_outliers_response: list[dict[str, Any]],
) -> None:
    """Validate get_institutional_outliers returns typed models."""
    client = Mock()
    client.post_json.return_value = sample_institutional_outliers_response

    results = get_institutional_outliers(
        client,
        end_date="2026-08-19",
        lookback_days=7,
        min_std=2.0,
    )

    client.post_json.assert_called_once_with(
        "/SectorBreakdown/GetInstitutionalOutliers",
        {"EndDate": "2026-08-19", "LookbackDays": 7, "MinSTD": 2.0},
    )
    assert len(results) == len(sample_institutional_outliers_response)
    assert results[0].ticker == "VCIT"


def test_get_notional_by_sector_by_name(
    sample_sector_themes_response: list[dict[str, Any]],
) -> None:
    """Validate get_notional_by_sector_by_name returns typed models."""
    client = Mock()
    client.post_json.return_value = sample_sector_themes_response

    results = get_notional_by_sector_by_name(
        client,
        end_date="2026-08-19",
        top_themes=10,
        top_tickers=10,
    )

    client.post_json.assert_called_once_with(
        "/SectorBreakdown/GetNotionalBySectorByName",
        {"EndDateKey": 20260819, "TopThemes": 10, "TopTickers": 10},
    )
    assert len(results) == len(sample_sector_themes_response)
    assert results[0].sector == "Technology"


def test_get_supply_demand_areas(
    sample_supply_demand_areas_response: list[dict[str, Any]],
) -> None:
    """Validate get_supply_demand_areas returns typed models."""
    client = Mock()
    client.post_json.return_value = sample_supply_demand_areas_response

    results = get_supply_demand_areas(
        client,
        start_date="2026-08-12",
        end_date="2026-08-19",
    )

    client.post_json.assert_called_once_with(
        "/SectorBreakdown/GetAutomatedSupplyAndDemandAreas",
        {"StartDateKey": 20260812, "EndDateKey": 20260819},
    )
    assert len(results) == len(sample_supply_demand_areas_response)
    assert results[0].sector == "Communication Services"


def test_get_sector_daily_returns(
    sample_sector_daily_returns_response: list[dict[str, Any]],
) -> None:
    """Validate get_sector_daily_returns returns typed models."""
    client = Mock()
    client.post_form.return_value = sample_sector_daily_returns_response

    results = get_sector_daily_returns(
        client,
        start_date="2025-02-19",
        end_date="2026-08-19",
    )

    client.post_form.assert_called_once_with(
        "/SectorBreakdown/GetSectorDailyReturns",
        "StartDate=2025-02-19&EndDate=2026-08-19",
    )
    assert len(results) == len(sample_sector_daily_returns_response)
    assert results[0].sector == "Bonds"
