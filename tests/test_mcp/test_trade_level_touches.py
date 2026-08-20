"""Tests for the trade_level_touches MCP tool."""

from __future__ import annotations

from importlib import import_module
from typing import Any
from unittest.mock import Mock

import pytest
from fastmcp import Client

_mcp_module = import_module("volumeleaders.mcp")
_tools = import_module("volumeleaders.mcp.tools.trade_level_touches")
_models = import_module("volumeleaders.models")

trade_level_touches_tool = _tools.trade_level_touches
TradeLevelTouch = _models.TradeLevelTouch

_curate_touch = vars(_tools)["_curate_touch"]
_format_time = vars(_tools)["_format_time"]
_resolve_filters = vars(_tools)["_resolve_filters"]

_DATE_LENGTH = 10
_BROAD_RELATIVE_SIZE = 5
_BROAD_RANK = 5
_BROAD_MIN_DOLLARS = 500_000_000
_TICKER_RANK = 10
_TICKER_MIN_DOLLARS = 500_000
_EXPLICIT_RELATIVE_SIZE = 2
_EXPLICIT_RANK = 20
_EXPLICIT_MIN_DOLLARS = 1_000_000
_PARTIAL_RELATIVE_SIZE = 3
_TOTAL_AVAILABLE = 1705


def _make_touches(
    sample_trade_level_touch_response: dict[str, Any],
) -> list[Any]:
    """Build TradeLevelTouch model rows from the real API fixture."""
    return [
        TradeLevelTouch.model_validate(row)
        for row in sample_trade_level_touch_response["data"]
    ]


# -- _format_time --------------------------------------------------------------


def test_format_time_from_time_string(
    sample_trade_level_touch_response: dict[str, Any],
) -> None:
    """Extract HH:MM from the 24-hour time string."""
    touch = TradeLevelTouch.model_validate(sample_trade_level_touch_response["data"][0])
    result = _format_time(touch)

    assert result == "17:51"


def test_format_time_fallback(
    sample_trade_level_touch_response: dict[str, Any],
) -> None:
    """Fall back to parsing FullDateTime when FullTimeString24 is None."""
    row = {**sample_trade_level_touch_response["data"][0], "FullTimeString24": None}
    touch = TradeLevelTouch.model_validate(row)
    result = _format_time(touch)

    assert result == "17:51"


# -- _curate_touch -------------------------------------------------------------


def test_curate_touch_field_set(
    sample_trade_level_touch_response: dict[str, Any],
) -> None:
    """Return exactly the expected compact fields from TradeLevelTouch model."""
    touch = TradeLevelTouch.model_validate(sample_trade_level_touch_response["data"][0])
    result = _curate_touch(touch)

    assert set(result) == {
        "ticker",
        "time",
        "price",
        "dollars",
        "volume",
        "trades",
        "rank",
        "relative_size",
        "level_origin_date",
        "level_last_confirmed",
    }


def test_curate_touch_preserves_values(
    sample_trade_level_touch_response: dict[str, Any],
) -> None:
    """Map model attributes to curated dict values correctly."""
    touch = TradeLevelTouch.model_validate(sample_trade_level_touch_response["data"][0])
    result = _curate_touch(touch)

    assert result["ticker"] == touch.ticker
    assert result["time"] == "17:51"
    assert result["price"] == touch.price
    assert result["dollars"] == "$738K"
    assert result["volume"] == touch.volume
    assert result["trades"] == touch.trades
    assert result["rank"] == touch.trade_level_rank
    assert result["relative_size"] == touch.relative_size


def test_curate_touch_dollars_formatted(
    sample_trade_level_touch_response: dict[str, Any],
) -> None:
    """Format dollars as a compact human-readable string."""
    touch = TradeLevelTouch.model_validate(sample_trade_level_touch_response["data"][0])
    result = _curate_touch(touch)

    # Fixture has Dollars: 738341.52; formatted to "$738K".
    assert isinstance(result["dollars"], str)
    assert result["dollars"] == "$738K"


def test_curate_touch_level_dates(
    sample_trade_level_touch_response: dict[str, Any],
) -> None:
    """Format min_date and max_date as self-documenting level date fields."""
    touch = TradeLevelTouch.model_validate(sample_trade_level_touch_response["data"][0])
    result = _curate_touch(touch)

    # Fixture has MinDate and MaxDate as ASP.NET dates; both should be
    # formatted as YYYY-MM-DD strings.
    assert result["level_origin_date"] is not None
    assert result["level_last_confirmed"] is not None
    assert len(result["level_origin_date"]) == _DATE_LENGTH
    assert len(result["level_last_confirmed"]) == _DATE_LENGTH


def test_curate_touch_omits_removed_fields(
    sample_trade_level_touch_response: dict[str, Any],
) -> None:
    """Exclude fields dropped for token efficiency."""
    touch = TradeLevelTouch.model_validate(sample_trade_level_touch_response["data"][0])
    result = _curate_touch(touch)

    assert "name" not in result
    assert "sector" not in result
    assert "industry" not in result
    assert "trade_level_touches" not in result
    assert "trade_level_rank" not in result  # renamed to "rank"
    assert "date_time" not in result  # replaced by compact "time"
    assert "dates" not in result  # replaced by level_origin_date/level_last_confirmed


# -- _resolve_filters ----------------------------------------------------------


def test_resolve_filters_broad_scan_defaults() -> None:
    """Apply tighter defaults when no tickers are specified."""
    rs, tlr, md = _resolve_filters(
        tickers="",
        relative_size=None,
        trade_level_rank=None,
        min_dollars=None,
    )

    assert rs == _BROAD_RELATIVE_SIZE
    assert tlr == _BROAD_RANK
    assert md == _BROAD_MIN_DOLLARS


def test_resolve_filters_ticker_defaults() -> None:
    """Apply permissive defaults when tickers are specified."""
    rs, tlr, md = _resolve_filters(
        tickers="AAPL",
        relative_size=None,
        trade_level_rank=None,
        min_dollars=None,
    )

    assert rs == 0
    assert tlr == _TICKER_RANK
    assert md == _TICKER_MIN_DOLLARS


def test_resolve_filters_explicit_values_win() -> None:
    """Explicit values override both default sets."""
    rs, tlr, md = _resolve_filters(
        tickers="",
        relative_size=_EXPLICIT_RELATIVE_SIZE,
        trade_level_rank=_EXPLICIT_RANK,
        min_dollars=_EXPLICIT_MIN_DOLLARS,
    )

    assert rs == _EXPLICIT_RELATIVE_SIZE
    assert tlr == _EXPLICIT_RANK
    assert md == _EXPLICIT_MIN_DOLLARS


def test_resolve_filters_partial_override() -> None:
    """Mix of explicit and default values resolves correctly."""
    rs, tlr, md = _resolve_filters(
        tickers="AAPL",
        relative_size=_PARTIAL_RELATIVE_SIZE,
        trade_level_rank=None,
        min_dollars=None,
    )

    assert rs == _PARTIAL_RELATIVE_SIZE
    assert tlr == _TICKER_RANK
    assert md == _TICKER_MIN_DOLLARS


# -- Tool integration tests ----------------------------------------------------


def test_envelope_shape_default(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_level_touch_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Return minimal envelope by default: data and metadata only."""
    touches = _make_touches(sample_trade_level_touch_response)
    monkeypatch.setattr(_tools, "get_trade_level_touches", lambda *_, **__: touches)

    result = trade_level_touches_tool(date="2026-04-02", ctx=mcp_context)

    # No warnings when endpoint succeeds.
    assert set(result) == {"data", "metadata"}
    assert set(result["data"]) == {"touches"}
    assert set(result["metadata"]) == {"touch_count", "total_available"}


def test_envelope_omits_warnings_when_empty(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_level_touch_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Omit the warnings key entirely when there are no warnings."""
    touches = _make_touches(sample_trade_level_touch_response)
    monkeypatch.setattr(_tools, "get_trade_level_touches", lambda *_, **__: touches)

    result = trade_level_touches_tool(date="2026-04-02", ctx=mcp_context)

    assert "warnings" not in result


def test_envelope_includes_warnings_when_present(
    monkeypatch: pytest.MonkeyPatch,
    mcp_context: object,
) -> None:
    """Include warnings key when endpoint fails."""
    monkeypatch.setattr(
        _tools,
        "get_trade_level_touches",
        Mock(side_effect=RuntimeError("Server error")),
    )

    result = trade_level_touches_tool(date="2026-04-02", ctx=mcp_context)

    assert "warnings" in result
    assert any("Failed to fetch trade level touches" in w for w in result["warnings"])


def test_curated_fields_in_response(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_level_touch_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Curate touch rows to the expected compact field set in tool response."""
    touches = _make_touches(sample_trade_level_touch_response)
    monkeypatch.setattr(_tools, "get_trade_level_touches", lambda *_, **__: touches)

    result = trade_level_touches_tool(date="2026-04-02", ctx=mcp_context)

    assert result["data"]["touches"] is not None
    assert len(result["data"]["touches"]) == 1
    assert set(result["data"]["touches"][0]) == {
        "ticker",
        "time",
        "price",
        "dollars",
        "volume",
        "trades",
        "rank",
        "relative_size",
        "level_origin_date",
        "level_last_confirmed",
    }


def test_default_date_uses_today(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_level_touch_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Use today's date when no date parameter is provided."""
    captured_kwargs: dict[str, Any] = {}

    def fake_endpoint(*_args: object, **kwargs: object) -> list[Any]:
        """Capture endpoint kwargs for assertion."""
        captured_kwargs.update(kwargs)
        return _make_touches(sample_trade_level_touch_response)

    monkeypatch.setattr(_tools, "get_trade_level_touches", fake_endpoint)
    monkeypatch.setattr(_tools, "today_date_string", lambda: "2026-04-02")

    trade_level_touches_tool(ctx=mcp_context)

    assert captured_kwargs["start_date"] == "2026-04-02"
    assert captured_kwargs["end_date"] == "2026-04-02"


def test_explicit_date_used(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_level_touch_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Use the provided date when explicitly passed."""
    captured_kwargs: dict[str, Any] = {}

    def fake_endpoint(*_args: object, **kwargs: object) -> list[Any]:
        """Capture endpoint kwargs for assertion."""
        captured_kwargs.update(kwargs)
        return _make_touches(sample_trade_level_touch_response)

    monkeypatch.setattr(_tools, "get_trade_level_touches", fake_endpoint)

    trade_level_touches_tool(date="2026-03-15", ctx=mcp_context)

    assert captured_kwargs["start_date"] == "2026-03-15"
    assert captured_kwargs["end_date"] == "2026-03-15"


def test_endpoint_failure_returns_null_with_warning(
    monkeypatch: pytest.MonkeyPatch,
    mcp_context: object,
) -> None:
    """Return touches as null with a warning when endpoint fails."""
    monkeypatch.setattr(
        _tools,
        "get_trade_level_touches",
        Mock(side_effect=RuntimeError("Server error")),
    )

    result = trade_level_touches_tool(date="2026-04-02", ctx=mcp_context)

    assert result["data"]["touches"] is None
    assert any("Failed to fetch trade level touches" in w for w in result["warnings"])


def test_tickers_filter_passed_to_endpoint(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_level_touch_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Pass ticker filter through to the endpoint function."""
    captured_kwargs: dict[str, Any] = {}

    def fake_endpoint(*_args: object, **kwargs: object) -> list[Any]:
        """Capture endpoint kwargs for assertion."""
        captured_kwargs.update(kwargs)
        return _make_touches(sample_trade_level_touch_response)

    monkeypatch.setattr(_tools, "get_trade_level_touches", fake_endpoint)

    trade_level_touches_tool(tickers="AAPL,MSFT", date="2026-04-02", ctx=mcp_context)

    assert captured_kwargs["tickers"] == "AAPL,MSFT"


def test_empty_result_returns_empty_list(
    monkeypatch: pytest.MonkeyPatch,
    mcp_context: object,
) -> None:
    """Return empty touches list when endpoint returns no rows."""
    monkeypatch.setattr(_tools, "get_trade_level_touches", lambda *_, **__: [])

    result = trade_level_touches_tool(date="2026-04-02", ctx=mcp_context)

    assert result["data"]["touches"] == []
    assert result["metadata"]["touch_count"] == 0
    assert result["metadata"]["total_available"] == 0


def test_metadata_counts(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_level_touch_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Include accurate count and total_available metadata."""
    touches = _make_touches(sample_trade_level_touch_response)
    monkeypatch.setattr(_tools, "get_trade_level_touches", lambda *_, **__: touches)

    result = trade_level_touches_tool(date="2026-04-02", ctx=mcp_context)

    assert result["metadata"]["touch_count"] == 1
    # TotalRows from fixture is 1705.
    assert result["metadata"]["total_available"] == _TOTAL_AVAILABLE


def test_metadata_null_on_failure(
    monkeypatch: pytest.MonkeyPatch,
    mcp_context: object,
) -> None:
    """Return null metadata when endpoint fails."""
    monkeypatch.setattr(
        _tools,
        "get_trade_level_touches",
        Mock(side_effect=RuntimeError("Timeout")),
    )

    result = trade_level_touches_tool(date="2026-04-02", ctx=mcp_context)

    assert result["metadata"]["touch_count"] is None
    assert result["metadata"]["total_available"] is None


@pytest.mark.asyncio
async def test_fastmcp_client_transport(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_level_touch_response: dict[str, Any],
) -> None:
    """Call the registered tool through FastMCP client transport."""

    class _FakeClient:
        """Test client object used for lifespan initialization."""

        def close(self) -> None:
            """Provide the close method expected by lifespan cleanup."""

    touches = _make_touches(sample_trade_level_touch_response)
    monkeypatch.setattr(_tools, "get_trade_level_touches", lambda *_, **__: touches)
    monkeypatch.setattr(_mcp_module, "VolumeLeadersClient", _FakeClient)

    async with Client(_mcp_module.mcp) as client:
        result = await client.call_tool(
            "trade_level_touches",
            {"date": "2026-04-02"},
        )

    assert result.data is not None
    assert result.data["data"]["touches"] is not None
