"""Tests for dark pool endpoint functions."""

from importlib import import_module
from typing import Any
from unittest.mock import Mock

get_dark_pool_volume_report = import_module(
    "volumeleaders.endpoints.darkpool",
).get_dark_pool_volume_report


def test_get_dark_pool_volume_report(
    sample_dark_pool_volume_report_response: list[dict[str, Any]],
) -> None:
    """Validate get_dark_pool_volume_report returns typed models."""
    client = Mock()
    client.post_json.return_value = sample_dark_pool_volume_report_response

    results = get_dark_pool_volume_report(
        client,
        last_trade_date="2026-08-19",
        start_date="2026-08-12",
        end_date="2026-08-19",
        bins=24,
        tickers="AAPL,MSFT",
    )

    client.post_json.assert_called_once_with(
        "/SectorBreakdown/GetDarkPoolVolumeReport",
        {
            "LastTradeDate": "2026-08-19",
            "StartDateKey": "20260812",
            "EndDateKey": "20260819",
            "Bins": 24,
            "Tickers": "AAPL,MSFT",
        },
    )
    assert len(results) == len(sample_dark_pool_volume_report_response)
    assert results[0].ticker == "AAPL"


def test_get_dark_pool_volume_report_empty_dates(
    sample_dark_pool_volume_report_response: list[dict[str, Any]],
) -> None:
    """Validate get_dark_pool_volume_report handles default date values."""
    client = Mock()
    client.post_json.return_value = sample_dark_pool_volume_report_response

    results = get_dark_pool_volume_report(
        client,
        last_trade_date="",
        start_date="20260812",
        end_date="",
        bins=24,
        tickers="AAPL",
    )

    client.post_json.assert_called_once_with(
        "/SectorBreakdown/GetDarkPoolVolumeReport",
        {
            "LastTradeDate": "",
            "StartDateKey": "20260812",
            "EndDateKey": "",
            "Bins": 24,
            "Tickers": "AAPL",
        },
    )
    assert len(results) == len(sample_dark_pool_volume_report_response)
