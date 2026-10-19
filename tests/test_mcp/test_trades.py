"""Tests for the trades MCP tool."""

from __future__ import annotations

from importlib import import_module
from typing import Any
from urllib.parse import parse_qs

import pytest
from fastmcp import Client

_mcp_module = import_module("volumeleaders.mcp")
_mcp_utils = import_module("volumeleaders.mcp.utils")
_tools = import_module("volumeleaders.mcp.tools.trades")
_models = import_module("volumeleaders.models")

trades_tool = _tools.trades
Trade = _models.Trade

_curate_trade = vars(_tools)["_curate_trade"]
_format_time = vars(_tools)["_format_time"]
_collect_trade_types = vars(_tools)["_collect_trade_types"]
_resolve_dates = vars(_tools)["_resolve_dates"]
_resolve_include_flags = vars(_tools)["_resolve_include_flags"]

_PRICE = 655.24
_CURRENT_PRICE = 655.01
_VOLUME = 482021
_UNRANKED = 9999
_DOLLARS_MULTIPLIER = 26.94
_DISTRIBUTION = 0.99
_TRADE_COUNT = 48
_DATE_LENGTH = 10
_RESULT_COUNT = 2
_DEFAULT_RANK = 100
_OFFSET = 20
_PAGE_SIZE = 10
_RANK_COLUMN = 11
_DOLLARS_COLUMN = 8
_MULTIPLIER_COLUMN = 9


# -- _format_time --------------------------------------------------------------


def test_format_time_from_time_string(
    sample_trade_response: dict[str, Any],
) -> None:
    """Extract HH:MM from the 24-hour time string."""
    trade = Trade.model_validate(sample_trade_response["data"][0])
    result = _format_time(trade)

    assert result == "17:18"


def test_format_time_fallback_to_full_datetime(
    sample_trade_response: dict[str, Any],
) -> None:
    """Fall back to parsing FullDateTime when FullTimeString24 is None."""
    row = {**sample_trade_response["data"][0], "FullTimeString24": None}
    trade = Trade.model_validate(row)
    result = _format_time(trade)

    assert result == "17:18"


def test_format_time_both_null(
    sample_trade_response: dict[str, Any],
) -> None:
    """Return empty string when both time fields are None."""
    row = {
        **sample_trade_response["data"][0],
        "FullTimeString24": None,
        "FullDateTime": None,
    }
    trade = Trade.model_validate(row)
    result = _format_time(trade)

    assert result == ""


# -- _collect_trade_types ------------------------------------------------------


def test_collect_trade_types_dark_pool(
    sample_trade_response: dict[str, Any],
) -> None:
    """Collect dark_pool flag from fixture data (DarkPool=1)."""
    trade = Trade.model_validate(sample_trade_response["data"][0])
    result = _collect_trade_types(trade)

    assert "dark_pool" in result


def test_collect_trade_types_no_flags_returns_block_sentinel(
    sample_trade_response: dict[str, Any],
) -> None:
    """Return ["block"] sentinel when no special type flags are set."""
    row = {
        **sample_trade_response["data"][0],
        "DarkPool": 0,
        "Sweep": 0,
        "LatePrint": 0,
        "SignaturePrint": 0,
        "OpeningTrade": 0,
        "ClosingTrade": 0,
        "PhantomPrint": 0,
    }
    trade = Trade.model_validate(row)
    result = _collect_trade_types(trade)

    assert result == ["block"]


def test_collect_trade_types_multiple_flags(
    sample_trade_response: dict[str, Any],
) -> None:
    """Collect multiple active flags into a single list."""
    row = {
        **sample_trade_response["data"][0],
        "DarkPool": 1,
        "Sweep": 1,
        "LatePrint": 1,
    }
    trade = Trade.model_validate(row)
    result = _collect_trade_types(trade)

    assert set(result) == {"dark_pool", "sweep", "late_print"}


# -- _curate_trade -------------------------------------------------------------


def test_curate_trade_field_set(
    sample_trade_response: dict[str, Any],
) -> None:
    """Return exactly the expected compact fields from Trade model."""
    trade = Trade.model_validate(sample_trade_response["data"][0])
    result = _curate_trade(trade, {})

    assert set(result) == {
        "ticker",
        "date",
        "time",
        "price",
        "current_price",
        "dollars",
        "volume",
        "trade_rank",
        "dollars_multiplier",
        "cumulative_distribution",
        "trade_count",
        "types",
        "sector",
        "last_comparable_date",
    }


def test_curate_trade_preserves_values(
    sample_trade_response: dict[str, Any],
) -> None:
    """Map model attributes to curated dict values correctly."""
    trade = Trade.model_validate(sample_trade_response["data"][0])
    result = _curate_trade(trade, {"SPY": 655.01})

    assert result["ticker"] == "SPY"
    assert result["time"] == "17:18"
    assert result["price"] == _PRICE
    assert result["current_price"] == _CURRENT_PRICE
    assert result["dollars"] == "$315.8M"
    assert result["volume"] == _VOLUME
    assert result["trade_rank"] == _UNRANKED
    assert result["dollars_multiplier"] == _DOLLARS_MULTIPLIER
    assert result["cumulative_distribution"] == _DISTRIBUTION
    assert result["trade_count"] == _TRADE_COUNT
    assert result["sector"] == "Large Caps"


def test_curate_trade_current_price_none_when_missing(
    sample_trade_response: dict[str, Any],
) -> None:
    """Return None for current_price when ticker not in snapshot map."""
    trade = Trade.model_validate(sample_trade_response["data"][0])
    result = _curate_trade(trade, {})

    assert result["current_price"] is None


def test_curate_trade_dollars_formatted(
    sample_trade_response: dict[str, Any],
) -> None:
    """Format dollars as a compact human-readable string."""
    trade = Trade.model_validate(sample_trade_response["data"][0])
    result = _curate_trade(trade, {})

    # Fixture has Dollars: 315839440.04; formatted to "$315.8M".
    assert isinstance(result["dollars"], str)
    assert result["dollars"] == "$315.8M"


def test_curate_trade_types_populated(
    sample_trade_response: dict[str, Any],
) -> None:
    """Include active trade type flags in types list."""
    trade = Trade.model_validate(sample_trade_response["data"][0])
    result = _curate_trade(trade, {})

    # Fixture has DarkPool=1, all others 0.
    assert result["types"] == ["dark_pool"]


def test_curate_trade_last_comparable_date(
    sample_trade_response: dict[str, Any],
) -> None:
    """Format LastComparibleTradeDate as YYYY-MM-DD string."""
    trade = Trade.model_validate(sample_trade_response["data"][0])
    result = _curate_trade(trade, {})

    assert result["last_comparable_date"] is not None
    assert len(result["last_comparable_date"]) == _DATE_LENGTH


def test_curate_trade_omits_removed_fields(
    sample_trade_response: dict[str, Any],
) -> None:
    """Exclude fields dropped for token efficiency."""
    trade = Trade.model_validate(sample_trade_response["data"][0])
    result = _curate_trade(trade, {})

    assert "name" not in result
    assert "industry" not in result
    assert "bid" not in result
    assert "ask" not in result
    assert "rsi_hour" not in result
    assert "rsi_day" not in result
    assert "trade_conditions" not in result


# -- _resolve_dates ------------------------------------------------------------


def test_resolve_dates_broad_scan_defaults() -> None:
    """Default to today for both start and end when no tickers."""
    start, end = _resolve_dates(tickers="", start_date="", end_date="")

    # Both should be today (same value).
    assert start == end


def test_resolve_dates_ticker_query_defaults(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Default to 90-day lookback when tickers are specified."""
    monkeypatch.setattr(_tools, "today_date_string", lambda: "2026-04-02")
    monkeypatch.setattr(_tools, "ninety_days_ago_date_string", lambda: "2026-01-02")

    start, end = _resolve_dates(tickers="AAPL", start_date="", end_date="")

    assert start == "2026-01-02"
    assert end == "2026-04-02"


def test_resolve_dates_explicit_values_win() -> None:
    """Explicit values override all defaults."""
    start, end = _resolve_dates(
        tickers="AAPL",
        start_date="2025-01-01",
        end_date="2025-06-01",
    )

    assert start == "2025-01-01"
    assert end == "2025-06-01"


def test_resolve_dates_explicit_start_only(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Explicit start_date with default end_date."""
    monkeypatch.setattr(_tools, "today_date_string", lambda: "2026-04-02")

    start, end = _resolve_dates(tickers="AAPL", start_date="2026-03-01", end_date="")

    assert start == "2026-03-01"
    assert end == "2026-04-02"


# -- _resolve_include_flags ----------------------------------------------------


def test_resolve_include_flags_broad_scan() -> None:
    """Exclude phantom and offsetting trades for broad scans."""
    phantom, offsetting = _resolve_include_flags(tickers="")

    assert phantom == -1
    assert offsetting == -1


def test_resolve_include_flags_ticker_query() -> None:
    """Include phantom and offsetting trades for ticker queries."""
    phantom, offsetting = _resolve_include_flags(tickers="AAPL")

    assert phantom == 1
    assert offsetting == 1


# -- Tool integration tests ----------------------------------------------------


def _serve_trades(
    client: object,
    sample_trade_response: dict[str, Any],
    *,
    snapshots: str = "",
) -> None:
    """Wire a mock client to serve the real trades and snapshot payloads."""
    client.post_datatables.return_value = sample_trade_response["data"]
    client.post_json.return_value = snapshots


def _last_trade_request(client: object) -> dict[str, list[str]]:
    """Return the parsed DataTables body from the latest trades request."""
    path, body = client.post_datatables.call_args.args
    assert path == "/Trades/GetTrades"
    return parse_qs(body, keep_blank_values=True)


def test_envelope_shape_default(
    sample_trade_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Return minimal envelope by default: data and metadata only."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _serve_trades(client, sample_trade_response)

    result = trades_tool(
        start_date="2026-04-01",
        end_date="2026-04-01",
        ctx=mcp_context,
    )

    # No warnings when endpoint succeeds.
    assert set(result) == {"data", "metadata"}
    assert set(result["data"]) == {"trades"}
    assert set(result["metadata"]) == {"trade_count", "total_available"}


def test_envelope_omits_warnings_when_empty(
    sample_trade_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Omit the warnings key entirely when there are no warnings."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _serve_trades(client, sample_trade_response)

    result = trades_tool(
        start_date="2026-04-01",
        end_date="2026-04-01",
        ctx=mcp_context,
    )

    assert "warnings" not in result


def test_envelope_includes_warnings_when_present(
    mcp_context: object,
) -> None:
    """Include warnings key when endpoint fails."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    client.post_datatables.side_effect = RuntimeError("Server error")

    result = trades_tool(
        start_date="2026-04-01",
        end_date="2026-04-01",
        ctx=mcp_context,
    )

    assert "warnings" in result
    assert any("Failed to fetch trades" in w for w in result["warnings"])


def test_curated_fields_in_response(
    sample_trade_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Curate trade rows to the expected compact field set in tool response."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _serve_trades(client, sample_trade_response)

    result = trades_tool(
        start_date="2026-04-01",
        end_date="2026-04-01",
        ctx=mcp_context,
    )

    assert result["data"]["trades"] is not None
    assert len(result["data"]["trades"]) == _RESULT_COUNT
    assert set(result["data"]["trades"][0]) == {
        "ticker",
        "date",
        "time",
        "price",
        "current_price",
        "dollars",
        "volume",
        "trade_rank",
        "dollars_multiplier",
        "cumulative_distribution",
        "trade_count",
        "types",
        "sector",
        "last_comparable_date",
    }


def test_default_dates_broad_scan(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Default to today for both dates on broad scans."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _serve_trades(client, sample_trade_response)
    monkeypatch.setattr(_tools, "today_date_string", lambda: "2026-04-02")

    trades_tool(ctx=mcp_context)

    request = _last_trade_request(client)
    assert request["StartDate"] == ["2026-04-02"]
    assert request["EndDate"] == ["2026-04-02"]


def test_default_dates_ticker_query(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Default to 90-day lookback for ticker-specific queries."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _serve_trades(client, sample_trade_response)
    monkeypatch.setattr(_tools, "today_date_string", lambda: "2026-04-02")
    monkeypatch.setattr(_tools, "ninety_days_ago_date_string", lambda: "2026-01-02")

    trades_tool(tickers="PL", ctx=mcp_context)

    request = _last_trade_request(client)
    assert request["StartDate"] == ["2026-01-02"]
    assert request["EndDate"] == ["2026-04-02"]


def test_explicit_dates_used(
    sample_trade_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Use explicit dates when provided."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _serve_trades(client, sample_trade_response)

    trades_tool(
        tickers="AAPL",
        start_date="2025-01-01",
        end_date="2026-03-15",
        ctx=mcp_context,
    )

    request = _last_trade_request(client)
    assert request["StartDate"] == ["2025-01-01"]
    assert request["EndDate"] == ["2026-03-15"]


def test_broad_scan_excludes_phantom_offsetting(
    sample_trade_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Broad scans default to excluding phantom and offsetting trades."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _serve_trades(client, sample_trade_response)

    trades_tool(start_date="2026-04-02", end_date="2026-04-02", ctx=mcp_context)

    request = _last_trade_request(client)
    assert request["IncludePhantom"] == ["-1"]
    assert request["IncludeOffsetting"] == ["-1"]


def test_ticker_query_includes_phantom_offsetting(
    sample_trade_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Ticker queries default to including phantom and offsetting trades."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _serve_trades(client, sample_trade_response)

    trades_tool(
        tickers="AAPL",
        start_date="2026-01-01",
        end_date="2026-04-02",
        ctx=mcp_context,
    )

    request = _last_trade_request(client)
    assert request["IncludePhantom"] == ["1"]
    assert request["IncludeOffsetting"] == ["1"]


def test_trade_rank_default(
    sample_trade_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Default trade_rank to 100 (ranked trades only)."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _serve_trades(client, sample_trade_response)

    trades_tool(start_date="2026-04-02", end_date="2026-04-02", ctx=mcp_context)

    request = _last_trade_request(client)
    assert request["TradeRank"] == [str(_DEFAULT_RANK)]


def test_tickers_filter_passed_to_endpoint(
    sample_trade_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Pass ticker filter through to the endpoint payload."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _serve_trades(client, sample_trade_response)

    trades_tool(
        tickers="AAPL,MSFT",
        start_date="2026-04-01",
        end_date="2026-04-01",
        ctx=mcp_context,
    )

    request = _last_trade_request(client)
    assert request["Tickers"] == ["AAPL,MSFT"]


def test_endpoint_failure_returns_null_with_warning(
    mcp_context: object,
) -> None:
    """Return trades as null with a warning when endpoint fails."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    client.post_datatables.side_effect = RuntimeError("Server error")

    result = trades_tool(
        start_date="2026-04-01",
        end_date="2026-04-01",
        ctx=mcp_context,
    )

    assert result["data"]["trades"] is None
    assert any("Failed to fetch trades" in w for w in result["warnings"])


def test_empty_result_returns_empty_list(
    mcp_context: object,
) -> None:
    """Return empty trades list when endpoint returns no rows."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    client.post_datatables.return_value = []
    client.post_json.return_value = ""

    result = trades_tool(
        start_date="2026-04-01",
        end_date="2026-04-01",
        ctx=mcp_context,
    )

    assert result["data"]["trades"] == []
    assert result["metadata"]["trade_count"] == 0
    assert result["metadata"]["total_available"] == 0


def test_metadata_counts(
    sample_trade_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Include accurate count and total_available metadata."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _serve_trades(client, sample_trade_response)

    result = trades_tool(
        start_date="2026-04-01",
        end_date="2026-04-01",
        ctx=mcp_context,
    )

    assert result["metadata"]["trade_count"] == _RESULT_COUNT
    # TotalRows from fixture is 48.
    assert result["metadata"]["total_available"] == _TRADE_COUNT


def test_metadata_null_on_failure(
    mcp_context: object,
) -> None:
    """Return null metadata when endpoint fails."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    client.post_datatables.side_effect = RuntimeError("Timeout")

    result = trades_tool(
        start_date="2026-04-01",
        end_date="2026-04-01",
        ctx=mcp_context,
    )

    assert result["metadata"]["trade_count"] is None
    assert result["metadata"]["total_available"] is None


def test_offset_passed_to_endpoint(
    sample_trade_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Pass offset through to the endpoint as start parameter."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _serve_trades(client, sample_trade_response)

    trades_tool(
        start_date="2026-04-01",
        end_date="2026-04-01",
        offset=_OFFSET,
        max_results=_PAGE_SIZE,
        ctx=mcp_context,
    )

    request = _last_trade_request(client)
    assert request["start"] == [str(_OFFSET)]
    assert request["length"] == [str(_PAGE_SIZE)]


def test_offset_defaults_to_zero(
    sample_trade_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Default offset to 0 when not specified."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _serve_trades(client, sample_trade_response)

    trades_tool(start_date="2026-04-01", end_date="2026-04-01", ctx=mcp_context)

    request = _last_trade_request(client)
    assert request["start"] == ["0"]


def test_sort_by_time_default(
    sample_trade_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Default sort by time descending (newest first)."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _serve_trades(client, sample_trade_response)

    trades_tool(start_date="2026-04-01", end_date="2026-04-01", ctx=mcp_context)

    request = _last_trade_request(client)
    assert request["order[0][column]"] == ["1"]
    assert request["order[0][dir]"] == ["desc"]


def test_sort_by_rank(
    sample_trade_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Sort by rank ascending (best rank first)."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _serve_trades(client, sample_trade_response)

    trades_tool(
        start_date="2026-04-01",
        end_date="2026-04-01",
        sort_by="rank",
        ctx=mcp_context,
    )

    request = _last_trade_request(client)
    assert request["order[0][column]"] == [str(_RANK_COLUMN)]
    assert request["order[0][dir]"] == ["asc"]


def test_sort_by_dollars(
    sample_trade_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Sort by dollars descending (biggest first)."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _serve_trades(client, sample_trade_response)

    trades_tool(
        start_date="2026-04-01",
        end_date="2026-04-01",
        sort_by="dollars",
        ctx=mcp_context,
    )

    request = _last_trade_request(client)
    assert request["order[0][column]"] == [str(_DOLLARS_COLUMN)]
    assert request["order[0][dir]"] == ["desc"]


def test_sort_by_multiplier(
    sample_trade_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Sort by multiplier descending (most unusual first)."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _serve_trades(client, sample_trade_response)

    trades_tool(
        start_date="2026-04-01",
        end_date="2026-04-01",
        sort_by="multiplier",
        ctx=mcp_context,
    )

    request = _last_trade_request(client)
    assert request["order[0][column]"] == [str(_MULTIPLIER_COLUMN)]
    assert request["order[0][dir]"] == ["desc"]


def test_sort_by_unknown_falls_back_to_time(
    sample_trade_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Fall back to time sort when sort_by value is unrecognized."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _serve_trades(client, sample_trade_response)

    trades_tool(
        start_date="2026-04-01",
        end_date="2026-04-01",
        sort_by="unknown",
        ctx=mcp_context,
    )

    request = _last_trade_request(client)
    assert request["order[0][column]"] == ["1"]
    assert request["order[0][dir]"] == ["desc"]


def test_snapshots_enrich_current_price(
    sample_trade_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Populate current_price from the real snapshot response parser."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _serve_trades(client, sample_trade_response, snapshots="SPY:655.01;")

    result = trades_tool(
        start_date="2026-04-01",
        end_date="2026-04-01",
        ctx=mcp_context,
    )

    assert result["data"]["trades"][0]["current_price"] == _CURRENT_PRICE


@pytest.mark.asyncio
async def test_fastmcp_client_transport(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_response: dict[str, Any],
) -> None:
    """Call the registered tool through FastMCP client transport."""

    class _FakeClient:
        """In-memory client serving the real trades endpoint payloads."""

        def post_datatables(self, _path: str, _body: str) -> list[dict[str, Any]]:
            """Serve the trades DataTables payload."""
            return sample_trade_response["data"]

        def post_json(self, _path: str, _payload: dict[str, Any]) -> str:
            """Serve an empty ticker snapshot map."""
            return ""

        def close(self) -> None:
            """Provide the close method expected by lifespan cleanup."""

    monkeypatch.setattr(_mcp_utils, "VolumeLeadersClient", _FakeClient)

    async with Client(_mcp_module.mcp) as client:
        result = await client.call_tool(
            "trades",
            {"start_date": "2026-04-01", "end_date": "2026-04-01"},
        )

    assert result.data is not None
    assert result.data["data"]["trades"] is not None
