"""Tests for chart endpoint helper functions."""

from importlib import import_module
from typing import Any
from unittest.mock import Mock

_chart = import_module("volumeleaders.endpoints.chart")
_models = import_module("volumeleaders.models")
get_chart_levels = _chart.get_chart_levels
get_chart_trades = _chart.get_chart_trades
ChartTrade = _models.ChartTrade
TradeLevel = _models.TradeLevel

_EXPECTED_FIRST_PRICE = 36.8
_REQUESTED_LEVELS = 10


def test_get_chart_levels_posts_json_and_returns_typed_models(
    sample_chart_trade_levels_response: list[dict[str, Any]],
) -> None:
    """POST the chart JSON payload and return a TradeLevel list."""
    client = Mock()
    client.post_json.return_value = sample_chart_trade_levels_response

    levels = get_chart_levels(
        client,
        ticker="CRDU",
        start_date="2026-05-19",
        end_date="20260520",
    )

    client.post_json.assert_called_once_with(
        "/Chart0/GetChartTradeLevels",
        {
            "StartDateKey": "20260519",
            "EndDateKey": "20260520",
            "Ticker": "CRDU",
            "Levels": 5,
        },
    )
    assert len(levels) == len(sample_chart_trade_levels_response)
    assert all(isinstance(level, TradeLevel) for level in levels)
    assert levels[0].price == _EXPECTED_FIRST_PRICE
    assert levels[0].ticker == "CRDU"


def test_get_chart_levels_uses_requested_level_count(
    sample_chart_trade_levels_response: list[dict[str, Any]],
) -> None:
    """Pass the caller's level count through to the API body."""
    client = Mock()
    client.post_json.return_value = sample_chart_trade_levels_response

    get_chart_levels(
        client,
        ticker="CRDU",
        start_date="20260519",
        end_date="20260520",
        levels=_REQUESTED_LEVELS,
    )

    body = client.post_json.call_args.args[1]
    assert body["Levels"] == _REQUESTED_LEVELS


def test_get_chart_levels_handles_non_list_response() -> None:
    """Return an empty list when the API does not return an array."""
    client = Mock()
    client.post_json.return_value = None

    levels = get_chart_levels(
        client,
        ticker="CRDU",
        start_date="20260519",
        end_date="20260520",
    )

    assert levels == []


def test_get_chart_trades_unwraps_envelope_index_one(
    sample_price_bar_response: list[Any],
) -> None:
    """POST the trades body and read the second sub-array (envelope index 1)."""
    client = Mock()
    client.post_json.return_value = sample_price_bar_response

    trades = get_chart_trades(
        client,
        ticker="SPY",
        start_date="2026-04-01",
        end_date="20260401",
    )

    client.post_json.assert_called_once()
    args = client.post_json.call_args.args
    assert args[0] == "/Chart0/GetAllPriceVolumeTradeData"
    assert args[1]["Ticker"] == "SPY"
    assert args[1]["StartDateKey"] == "20260401"
    assert args[1]["EndDateKey"] == "20260401"
    assert args[1]["Levels"] == 5
    assert args[1]["TradeCount"] == 5
    assert len(trades) == len(sample_price_bar_response[1])
    assert all(isinstance(t, ChartTrade) for t in trades)


def test_get_chart_trades_handles_short_envelope() -> None:
    """Return an empty list when the response has no index-1 sub-array."""
    client = Mock()
    client.post_json.return_value = [[{"placeholder": True}]]

    trades = get_chart_trades(
        client,
        ticker="SPY",
        start_date="2026-04-01",
        end_date="20260401",
    )

    assert trades == []


def test_get_chart_trades_handles_non_list_response() -> None:
    """Return an empty list when the API does not return an array."""
    client = Mock()
    client.post_json.return_value = None

    trades = get_chart_trades(
        client,
        ticker="SPY",
        start_date="2026-04-01",
        end_date="20260401",
    )

    assert trades == []
