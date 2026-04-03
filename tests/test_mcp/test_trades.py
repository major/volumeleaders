"""Tests for the trades MCP tool."""

from __future__ import annotations

from importlib import import_module
from typing import Any
from unittest.mock import Mock

import pytest

_mcp_module = import_module("volumeleaders.mcp")
_tools = import_module("volumeleaders.mcp.tools.trades")
_models = import_module("volumeleaders.models")

trades_tool = _tools.trades
Trade = _models.Trade

_curate_trade = _tools._curate_trade
_format_time = _tools._format_time
_collect_trade_types = _tools._collect_trade_types
_resolve_dates = _tools._resolve_dates
_resolve_include_flags = _tools._resolve_include_flags


def _make_trades(
    sample_trade_response: dict[str, Any],
) -> list[Any]:
    """Build Trade model rows from the real API fixture."""
    return [Trade.model_validate(row) for row in sample_trade_response["data"]]


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
    assert result["price"] == 655.24
    assert result["current_price"] == 655.01
    assert result["dollars"] == "$315.8M"
    assert result["volume"] == 482021
    assert result["trade_rank"] == 9999
    assert result["dollars_multiplier"] == 26.94
    assert result["cumulative_distribution"] == 0.99
    assert result["trade_count"] == 48
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
    assert len(result["last_comparable_date"]) == 10


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
        tickers="AAPL", start_date="2025-01-01", end_date="2025-06-01"
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


def test_envelope_shape_default(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_response: dict[str, Any],
    mcp_context: Any,
) -> None:
    """Return minimal envelope by default: data and metadata only."""
    raw_trades = _make_trades(sample_trade_response)
    monkeypatch.setattr(_tools, "get_trades", lambda *a, **kw: raw_trades)
    monkeypatch.setattr(_tools, "fetch_snapshot_prices", lambda *a, **kw: {})

    result = trades_tool(
        start_date="2026-04-01", end_date="2026-04-01", ctx=mcp_context
    )

    # No warnings when endpoint succeeds.
    assert set(result) == {"data", "metadata"}
    assert set(result["data"]) == {"trades"}
    assert set(result["metadata"]) == {"trade_count", "total_available"}


def test_envelope_omits_warnings_when_empty(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_response: dict[str, Any],
    mcp_context: Any,
) -> None:
    """Omit the warnings key entirely when there are no warnings."""
    raw_trades = _make_trades(sample_trade_response)
    monkeypatch.setattr(_tools, "get_trades", lambda *a, **kw: raw_trades)
    monkeypatch.setattr(_tools, "fetch_snapshot_prices", lambda *a, **kw: {})

    result = trades_tool(
        start_date="2026-04-01", end_date="2026-04-01", ctx=mcp_context
    )

    assert "warnings" not in result


def test_envelope_includes_warnings_when_present(
    monkeypatch: pytest.MonkeyPatch,
    mcp_context: Any,
) -> None:
    """Include warnings key when endpoint fails."""
    monkeypatch.setattr(
        _tools,
        "get_trades",
        Mock(side_effect=RuntimeError("Server error")),
    )

    result = trades_tool(
        start_date="2026-04-01", end_date="2026-04-01", ctx=mcp_context
    )

    assert "warnings" in result
    assert any("Failed to fetch trades" in w for w in result["warnings"])


def test_curated_fields_in_response(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_response: dict[str, Any],
    mcp_context: Any,
) -> None:
    """Curate trade rows to the expected compact field set in tool response."""
    raw_trades = _make_trades(sample_trade_response)
    monkeypatch.setattr(_tools, "get_trades", lambda *a, **kw: raw_trades)
    monkeypatch.setattr(_tools, "fetch_snapshot_prices", lambda *a, **kw: {})

    result = trades_tool(
        start_date="2026-04-01", end_date="2026-04-01", ctx=mcp_context
    )

    assert result["data"]["trades"] is not None
    assert len(result["data"]["trades"]) == 2
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
    mcp_context: Any,
) -> None:
    """Default to today for both dates on broad scans."""
    captured_kwargs: dict[str, Any] = {}

    def fake_endpoint(*args: Any, **kwargs: Any) -> list[Any]:
        """Capture endpoint kwargs for assertion."""
        captured_kwargs.update(kwargs)
        return _make_trades(sample_trade_response)

    monkeypatch.setattr(_tools, "get_trades", fake_endpoint)
    monkeypatch.setattr(_tools, "fetch_snapshot_prices", lambda *a, **kw: {})
    monkeypatch.setattr(_tools, "today_date_string", lambda: "2026-04-02")

    trades_tool(ctx=mcp_context)

    assert captured_kwargs["start_date"] == "2026-04-02"
    assert captured_kwargs["end_date"] == "2026-04-02"


def test_default_dates_ticker_query(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_response: dict[str, Any],
    mcp_context: Any,
) -> None:
    """Default to 90-day lookback for ticker-specific queries."""
    captured_kwargs: dict[str, Any] = {}

    def fake_endpoint(*args: Any, **kwargs: Any) -> list[Any]:
        """Capture endpoint kwargs for assertion."""
        captured_kwargs.update(kwargs)
        return _make_trades(sample_trade_response)

    monkeypatch.setattr(_tools, "get_trades", fake_endpoint)
    monkeypatch.setattr(_tools, "fetch_snapshot_prices", lambda *a, **kw: {})
    monkeypatch.setattr(_tools, "today_date_string", lambda: "2026-04-02")
    monkeypatch.setattr(_tools, "ninety_days_ago_date_string", lambda: "2026-01-02")

    trades_tool(tickers="PL", ctx=mcp_context)

    assert captured_kwargs["start_date"] == "2026-01-02"
    assert captured_kwargs["end_date"] == "2026-04-02"


def test_explicit_dates_used(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_response: dict[str, Any],
    mcp_context: Any,
) -> None:
    """Use explicit dates when provided."""
    captured_kwargs: dict[str, Any] = {}

    def fake_endpoint(*args: Any, **kwargs: Any) -> list[Any]:
        """Capture endpoint kwargs for assertion."""
        captured_kwargs.update(kwargs)
        return _make_trades(sample_trade_response)

    monkeypatch.setattr(_tools, "get_trades", fake_endpoint)
    monkeypatch.setattr(_tools, "fetch_snapshot_prices", lambda *a, **kw: {})

    trades_tool(
        tickers="AAPL",
        start_date="2025-01-01",
        end_date="2026-03-15",
        ctx=mcp_context,
    )

    assert captured_kwargs["start_date"] == "2025-01-01"
    assert captured_kwargs["end_date"] == "2026-03-15"


def test_broad_scan_excludes_phantom_offsetting(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_response: dict[str, Any],
    mcp_context: Any,
) -> None:
    """Broad scans default to excluding phantom and offsetting trades."""
    captured_kwargs: dict[str, Any] = {}

    def fake_endpoint(*args: Any, **kwargs: Any) -> list[Any]:
        """Capture endpoint kwargs for assertion."""
        captured_kwargs.update(kwargs)
        return _make_trades(sample_trade_response)

    monkeypatch.setattr(_tools, "get_trades", fake_endpoint)
    monkeypatch.setattr(_tools, "fetch_snapshot_prices", lambda *a, **kw: {})

    trades_tool(start_date="2026-04-02", end_date="2026-04-02", ctx=mcp_context)

    assert captured_kwargs["include_phantom"] == -1
    assert captured_kwargs["include_offsetting"] == -1


def test_ticker_query_includes_phantom_offsetting(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_response: dict[str, Any],
    mcp_context: Any,
) -> None:
    """Ticker queries default to including phantom and offsetting trades."""
    captured_kwargs: dict[str, Any] = {}

    def fake_endpoint(*args: Any, **kwargs: Any) -> list[Any]:
        """Capture endpoint kwargs for assertion."""
        captured_kwargs.update(kwargs)
        return _make_trades(sample_trade_response)

    monkeypatch.setattr(_tools, "get_trades", fake_endpoint)
    monkeypatch.setattr(_tools, "fetch_snapshot_prices", lambda *a, **kw: {})

    trades_tool(
        tickers="AAPL", start_date="2026-01-01", end_date="2026-04-02", ctx=mcp_context
    )

    assert captured_kwargs["include_phantom"] == 1
    assert captured_kwargs["include_offsetting"] == 1


def test_trade_rank_default(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_response: dict[str, Any],
    mcp_context: Any,
) -> None:
    """Default trade_rank to 100 (ranked trades only)."""
    captured_kwargs: dict[str, Any] = {}

    def fake_endpoint(*args: Any, **kwargs: Any) -> list[Any]:
        """Capture endpoint kwargs for assertion."""
        captured_kwargs.update(kwargs)
        return _make_trades(sample_trade_response)

    monkeypatch.setattr(_tools, "get_trades", fake_endpoint)
    monkeypatch.setattr(_tools, "fetch_snapshot_prices", lambda *a, **kw: {})

    trades_tool(start_date="2026-04-02", end_date="2026-04-02", ctx=mcp_context)

    assert captured_kwargs["trade_rank"] == 100


def test_tickers_filter_passed_to_endpoint(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_response: dict[str, Any],
    mcp_context: Any,
) -> None:
    """Pass ticker filter through to the endpoint function."""
    captured_kwargs: dict[str, Any] = {}

    def fake_endpoint(*args: Any, **kwargs: Any) -> list[Any]:
        """Capture endpoint kwargs for assertion."""
        captured_kwargs.update(kwargs)
        return _make_trades(sample_trade_response)

    monkeypatch.setattr(_tools, "get_trades", fake_endpoint)
    monkeypatch.setattr(_tools, "fetch_snapshot_prices", lambda *a, **kw: {})

    trades_tool(
        tickers="AAPL,MSFT",
        start_date="2026-04-01",
        end_date="2026-04-01",
        ctx=mcp_context,
    )

    assert captured_kwargs["tickers"] == "AAPL,MSFT"


def test_endpoint_failure_returns_null_with_warning(
    monkeypatch: pytest.MonkeyPatch,
    mcp_context: Any,
) -> None:
    """Return trades as null with a warning when endpoint fails."""
    monkeypatch.setattr(
        _tools,
        "get_trades",
        Mock(side_effect=RuntimeError("Server error")),
    )

    result = trades_tool(
        start_date="2026-04-01", end_date="2026-04-01", ctx=mcp_context
    )

    assert result["data"]["trades"] is None
    assert any("Failed to fetch trades" in w for w in result["warnings"])


def test_empty_result_returns_empty_list(
    monkeypatch: pytest.MonkeyPatch,
    mcp_context: Any,
) -> None:
    """Return empty trades list when endpoint returns no rows."""
    monkeypatch.setattr(_tools, "get_trades", lambda *a, **kw: [])
    monkeypatch.setattr(_tools, "fetch_snapshot_prices", lambda *a, **kw: {})

    result = trades_tool(
        start_date="2026-04-01", end_date="2026-04-01", ctx=mcp_context
    )

    assert result["data"]["trades"] == []
    assert result["metadata"]["trade_count"] == 0
    assert result["metadata"]["total_available"] == 0


def test_metadata_counts(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_response: dict[str, Any],
    mcp_context: Any,
) -> None:
    """Include accurate count and total_available metadata."""
    raw_trades = _make_trades(sample_trade_response)
    monkeypatch.setattr(_tools, "get_trades", lambda *a, **kw: raw_trades)
    monkeypatch.setattr(_tools, "fetch_snapshot_prices", lambda *a, **kw: {})

    result = trades_tool(
        start_date="2026-04-01", end_date="2026-04-01", ctx=mcp_context
    )

    assert result["metadata"]["trade_count"] == 2
    # TotalRows from fixture is 48.
    assert result["metadata"]["total_available"] == 48


def test_metadata_null_on_failure(
    monkeypatch: pytest.MonkeyPatch,
    mcp_context: Any,
) -> None:
    """Return null metadata when endpoint fails."""
    monkeypatch.setattr(
        _tools,
        "get_trades",
        Mock(side_effect=RuntimeError("Timeout")),
    )

    result = trades_tool(
        start_date="2026-04-01", end_date="2026-04-01", ctx=mcp_context
    )

    assert result["metadata"]["trade_count"] is None
    assert result["metadata"]["total_available"] is None


def test_offset_passed_to_endpoint(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_response: dict[str, Any],
    mcp_context: Any,
) -> None:
    """Pass offset through to the endpoint as start parameter."""
    captured_kwargs: dict[str, Any] = {}

    def fake_endpoint(*args: Any, **kwargs: Any) -> list[Any]:
        """Capture endpoint kwargs for assertion."""
        captured_kwargs.update(kwargs)
        return _make_trades(sample_trade_response)

    monkeypatch.setattr(_tools, "get_trades", fake_endpoint)
    monkeypatch.setattr(_tools, "fetch_snapshot_prices", lambda *a, **kw: {})

    trades_tool(
        start_date="2026-04-01",
        end_date="2026-04-01",
        offset=20,
        max_results=10,
        ctx=mcp_context,
    )

    assert captured_kwargs["start"] == 20
    assert captured_kwargs["length"] == 10


def test_offset_defaults_to_zero(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_response: dict[str, Any],
    mcp_context: Any,
) -> None:
    """Default offset to 0 when not specified."""
    captured_kwargs: dict[str, Any] = {}

    def fake_endpoint(*args: Any, **kwargs: Any) -> list[Any]:
        """Capture endpoint kwargs for assertion."""
        captured_kwargs.update(kwargs)
        return _make_trades(sample_trade_response)

    monkeypatch.setattr(_tools, "get_trades", fake_endpoint)
    monkeypatch.setattr(_tools, "fetch_snapshot_prices", lambda *a, **kw: {})

    trades_tool(start_date="2026-04-01", end_date="2026-04-01", ctx=mcp_context)

    assert captured_kwargs["start"] == 0


def test_sort_by_time_default(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_response: dict[str, Any],
    mcp_context: Any,
) -> None:
    """Default sort by time descending (newest first)."""
    captured_kwargs: dict[str, Any] = {}

    def fake_endpoint(*args: Any, **kwargs: Any) -> list[Any]:
        """Capture endpoint kwargs for assertion."""
        captured_kwargs.update(kwargs)
        return _make_trades(sample_trade_response)

    monkeypatch.setattr(_tools, "get_trades", fake_endpoint)
    monkeypatch.setattr(_tools, "fetch_snapshot_prices", lambda *a, **kw: {})

    trades_tool(start_date="2026-04-01", end_date="2026-04-01", ctx=mcp_context)

    assert captured_kwargs["order_column_index"] == 1
    assert captured_kwargs["order_direction"] == "desc"


def test_sort_by_rank(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_response: dict[str, Any],
    mcp_context: Any,
) -> None:
    """Sort by rank ascending (best rank first)."""
    captured_kwargs: dict[str, Any] = {}

    def fake_endpoint(*args: Any, **kwargs: Any) -> list[Any]:
        """Capture endpoint kwargs for assertion."""
        captured_kwargs.update(kwargs)
        return _make_trades(sample_trade_response)

    monkeypatch.setattr(_tools, "get_trades", fake_endpoint)
    monkeypatch.setattr(_tools, "fetch_snapshot_prices", lambda *a, **kw: {})

    trades_tool(
        start_date="2026-04-01",
        end_date="2026-04-01",
        sort_by="rank",
        ctx=mcp_context,
    )

    assert captured_kwargs["order_column_index"] == 11
    assert captured_kwargs["order_direction"] == "asc"


def test_sort_by_dollars(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_response: dict[str, Any],
    mcp_context: Any,
) -> None:
    """Sort by dollars descending (biggest first)."""
    captured_kwargs: dict[str, Any] = {}

    def fake_endpoint(*args: Any, **kwargs: Any) -> list[Any]:
        """Capture endpoint kwargs for assertion."""
        captured_kwargs.update(kwargs)
        return _make_trades(sample_trade_response)

    monkeypatch.setattr(_tools, "get_trades", fake_endpoint)
    monkeypatch.setattr(_tools, "fetch_snapshot_prices", lambda *a, **kw: {})

    trades_tool(
        start_date="2026-04-01",
        end_date="2026-04-01",
        sort_by="dollars",
        ctx=mcp_context,
    )

    assert captured_kwargs["order_column_index"] == 8
    assert captured_kwargs["order_direction"] == "desc"


def test_sort_by_multiplier(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_response: dict[str, Any],
    mcp_context: Any,
) -> None:
    """Sort by multiplier descending (most unusual first)."""
    captured_kwargs: dict[str, Any] = {}

    def fake_endpoint(*args: Any, **kwargs: Any) -> list[Any]:
        """Capture endpoint kwargs for assertion."""
        captured_kwargs.update(kwargs)
        return _make_trades(sample_trade_response)

    monkeypatch.setattr(_tools, "get_trades", fake_endpoint)
    monkeypatch.setattr(_tools, "fetch_snapshot_prices", lambda *a, **kw: {})

    trades_tool(
        start_date="2026-04-01",
        end_date="2026-04-01",
        sort_by="multiplier",
        ctx=mcp_context,
    )

    assert captured_kwargs["order_column_index"] == 9
    assert captured_kwargs["order_direction"] == "desc"


def test_sort_by_unknown_falls_back_to_time(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_response: dict[str, Any],
    mcp_context: Any,
) -> None:
    """Fall back to time sort when sort_by value is unrecognized."""
    captured_kwargs: dict[str, Any] = {}

    def fake_endpoint(*args: Any, **kwargs: Any) -> list[Any]:
        """Capture endpoint kwargs for assertion."""
        captured_kwargs.update(kwargs)
        return _make_trades(sample_trade_response)

    monkeypatch.setattr(_tools, "get_trades", fake_endpoint)
    monkeypatch.setattr(_tools, "fetch_snapshot_prices", lambda *a, **kw: {})

    trades_tool(
        start_date="2026-04-01",
        end_date="2026-04-01",
        sort_by="unknown",
        ctx=mcp_context,
    )

    assert captured_kwargs["order_column_index"] == 1
    assert captured_kwargs["order_direction"] == "desc"


def test_snapshots_enrich_current_price(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_response: dict[str, Any],
    mcp_context: Any,
) -> None:
    """Populate current_price from snapshot data."""
    raw_trades = _make_trades(sample_trade_response)
    monkeypatch.setattr(_tools, "get_trades", lambda *a, **kw: raw_trades)
    monkeypatch.setattr(
        _tools,
        "fetch_snapshot_prices",
        lambda *a, **kw: {"SPY": 655.01},
    )

    result = trades_tool(
        start_date="2026-04-01", end_date="2026-04-01", ctx=mcp_context
    )

    assert result["data"]["trades"][0]["current_price"] == 655.01


@pytest.mark.asyncio
async def test_fastmcp_client_transport(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_response: dict[str, Any],
) -> None:
    """Call the registered tool through FastMCP client transport."""
    from fastmcp import Client

    class _FakeClient:
        """Test client object used for lifespan initialization."""

        def close(self) -> None:
            """Provide the close method expected by lifespan cleanup."""

    raw_trades = _make_trades(sample_trade_response)
    monkeypatch.setattr(_tools, "get_trades", lambda *a, **kw: raw_trades)
    monkeypatch.setattr(_tools, "fetch_snapshot_prices", lambda *a, **kw: {})
    monkeypatch.setattr(_mcp_module, "VolumeLeadersClient", _FakeClient)

    async with Client(_mcp_module.mcp) as client:
        result = await client.call_tool(
            "trades",
            {"start_date": "2026-04-01", "end_date": "2026-04-01"},
        )

    assert result.data is not None
    assert result.data["data"]["trades"] is not None
