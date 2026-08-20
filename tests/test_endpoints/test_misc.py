"""Tests for endpoint functions outside the trade and exhaustion domains."""

from importlib import import_module
from typing import Any
from unittest.mock import Mock

_alerts = import_module("volumeleaders.endpoints.alerts")
_chart = import_module("volumeleaders.endpoints.chart")
_earnings = import_module("volumeleaders.endpoints.earnings")
_levels = import_module("volumeleaders.endpoints.levels")
_volume = import_module("volumeleaders.endpoints.volume")
_watchlist = import_module("volumeleaders.endpoints.watchlist")
_models = import_module("volumeleaders.models")


def test_alert_endpoints_return_empty_lists() -> None:
    """Build requests for alert endpoints when no rows are returned."""
    client = Mock()
    client.post_datatables.return_value = []

    assert _alerts.get_alert_configs(client) == []
    assert _alerts.get_trade_alerts(client, date="2026-04-01") == []
    assert _alerts.get_trade_cluster_alerts(client, date="2026-04-01") == []


def test_chart_endpoints_validate_fixture_models(
    sample_company_response: dict[str, Any],
    sample_snapshot_response: dict[str, Any],
    sample_price_bar_response: list[Any],
    sample_trade_level_response: dict[str, Any],
) -> None:
    """Transform chart JSON, DataTables, and date-key requests into models."""
    client = Mock()
    client.post_json.side_effect = [
        sample_price_bar_response,
        sample_snapshot_response,
        sample_company_response,
    ]
    client.post_datatables.return_value = sample_trade_level_response["data"]

    price_bars = _chart.get_price_data(
        client,
        ticker="SPY",
        start_date="20260401",
        end_date="2026-04-01",
    )
    snapshot = _chart.get_snapshot(client, ticker="SPY", date_key="2026-04-01")
    company = _chart.get_company(client, ticker="SPY")
    levels = _chart.get_chart_levels(
        client,
        ticker="AMD",
        start_date="2026-04-01",
        end_date="2026-04-02",
    )

    assert isinstance(price_bars[0], _models.PriceBar)
    assert isinstance(snapshot, _models.Snapshot)
    assert isinstance(company, _models.Company)
    assert isinstance(levels[0], _models.TradeLevel)


def test_earnings_endpoint_validates_fixture(
    sample_earnings_response: dict[str, Any],
) -> None:
    """Transform earnings DataTables rows into typed models."""
    client = Mock()
    client.post_datatables.return_value = sample_earnings_response["data"]

    result = _earnings.get_earnings(
        client,
        start_date="2026-04-01",
        end_date="2026-04-02",
    )

    assert isinstance(result[0], _models.Earnings)


def test_level_endpoints_validate_fixtures(
    sample_trade_level_response: dict[str, Any],
    sample_trade_level_touch_response: dict[str, Any],
) -> None:
    """Transform trade-level and touch rows into typed models."""
    client = Mock()
    client.post_datatables.side_effect = [
        sample_trade_level_response["data"],
        sample_trade_level_touch_response["data"],
    ]

    levels = _levels.get_trade_levels(
        client,
        ticker="AMD",
        start_date="2026-04-01",
        end_date="2026-04-02",
    )
    touches = _levels.get_trade_level_touches(
        client,
        tickers="WTID",
        start_date="2026-04-01",
        end_date="2026-04-02",
    )

    assert isinstance(levels[0], _models.TradeLevel)
    assert isinstance(touches[0], _models.TradeLevelTouch)


def test_volume_endpoints_validate_fixture(
    sample_institutional_volume_response: dict[str, Any],
) -> None:
    """Transform institutional and total volume rows into typed models."""
    client = Mock()
    client.post_datatables.return_value = sample_institutional_volume_response["data"]

    institutional = _volume.get_institutional_volume(client, date="2026-04-01")
    after_hours = _volume.get_ah_institutional_volume(client, date="2026-04-01")
    total = _volume.get_total_volume(client, date="2026-04-01")

    assert isinstance(institutional[0], _models.InstitutionalVolume)
    assert isinstance(after_hours[0], _models.InstitutionalVolume)
    assert isinstance(total[0], _models.TotalVolume)


def test_watchlist_endpoints_validate_config_fixture(
    sample_watchlist_config_response: dict[str, Any],
) -> None:
    """Transform watchlist configs and handle an empty ticker response."""
    client = Mock()
    client.post_datatables.side_effect = [
        [],
        sample_watchlist_config_response["data"],
    ]

    tickers = _watchlist.get_watchlist_tickers(client)
    configs = _watchlist.get_watchlist_configs(client)

    assert tickers == []
    assert isinstance(configs[0], _models.WatchListConfig)
