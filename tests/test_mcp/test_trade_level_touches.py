"""Tests for the trade_level_touches MCP tool."""

from __future__ import annotations

from importlib import import_module
from typing import Any
from urllib.parse import parse_qs

import pytest
from fastmcp import Client

_mcp_module = import_module("volumeleaders.mcp")
_mcp_utils = import_module("volumeleaders.mcp.utils")
_tools = import_module("volumeleaders.mcp.tools.trade_level_touches")

trade_level_touches_tool = _tools.trade_level_touches

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
_TOUCH_PRICE = 4.6
_TOUCH_VOLUME = 161917


# -- Tool integration tests ----------------------------------------------------


def _serve_touches(
    client: object,
    sample_trade_level_touch_response: dict[str, Any],
    *,
    row_overrides: dict[str, Any] | None = None,
) -> None:
    """Wire a mock client to serve the real trade level touch payload.

    ``row_overrides`` replaces fields on the fixture rows before serving,
    so edge cases reuse the real payload shape instead of synthetic rows.
    """
    rows = sample_trade_level_touch_response["data"]
    if row_overrides is not None:
        rows = [{**row, **row_overrides} for row in rows]
    client.post_datatables.return_value = rows


def _last_touch_request(client: object) -> dict[str, list[str]]:
    """Return the parsed DataTables body from the latest touches request."""
    path, body = client.post_datatables.call_args.args
    assert path == "/TradeLevelTouches/GetTradeLevelTouches"
    return parse_qs(body, keep_blank_values=True)


def test_envelope_shape_default(
    sample_trade_level_touch_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Return minimal envelope by default: data and metadata only."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _serve_touches(client, sample_trade_level_touch_response)

    result = trade_level_touches_tool(date="2026-04-02", ctx=mcp_context)

    # No warnings when endpoint succeeds.
    assert set(result) == {"data", "metadata"}
    assert set(result["data"]) == {"touches"}
    assert set(result["metadata"]) == {"touch_count", "total_available"}


def test_envelope_omits_warnings_when_empty(
    sample_trade_level_touch_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Omit the warnings key entirely when there are no warnings."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _serve_touches(client, sample_trade_level_touch_response)

    result = trade_level_touches_tool(date="2026-04-02", ctx=mcp_context)

    assert "warnings" not in result


def test_envelope_includes_warnings_when_present(
    mcp_context: object,
) -> None:
    """Include warnings key when endpoint fails."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    client.post_datatables.side_effect = RuntimeError("Server error")

    result = trade_level_touches_tool(date="2026-04-02", ctx=mcp_context)

    assert "warnings" in result
    assert any("Failed to fetch trade level touches" in w for w in result["warnings"])


def test_curated_fields_in_response(
    sample_trade_level_touch_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Curate touch rows to the expected compact field set in tool response."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _serve_touches(client, sample_trade_level_touch_response)

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


def test_curated_time_from_time_string(
    sample_trade_level_touch_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Expose HH:MM from the 24-hour time string in the curated time field."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _serve_touches(client, sample_trade_level_touch_response)

    result = trade_level_touches_tool(date="2026-04-02", ctx=mcp_context)

    assert result["data"]["touches"][0]["time"] == "17:51"


def test_curated_time_falls_back_to_full_datetime(
    sample_trade_level_touch_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Fall back to parsing FullDateTime when FullTimeString24 is missing."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _serve_touches(
        client,
        sample_trade_level_touch_response,
        row_overrides={"FullTimeString24": None},
    )

    result = trade_level_touches_tool(date="2026-04-02", ctx=mcp_context)

    assert result["data"]["touches"][0]["time"] == "17:51"


def test_curated_values_in_response(
    sample_trade_level_touch_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Map model attributes to curated touch values in the response."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _serve_touches(client, sample_trade_level_touch_response)

    result = trade_level_touches_tool(date="2026-04-02", ctx=mcp_context)

    touch = result["data"]["touches"][0]
    assert touch["ticker"] == "WTID"
    assert touch["time"] == "17:51"
    assert touch["price"] == _TOUCH_PRICE
    assert touch["dollars"] == "$738K"
    assert touch["volume"] == _TOUCH_VOLUME
    assert touch["trades"] == 1
    assert touch["rank"] == 1
    assert touch["relative_size"] == 1
    assert touch["level_origin_date"] == "2026-03-23"
    assert touch["level_last_confirmed"] == "2026-03-23"


def test_broad_scan_filter_defaults(
    sample_trade_level_touch_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Apply tighter filter defaults when no tickers are specified."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _serve_touches(client, sample_trade_level_touch_response)

    trade_level_touches_tool(date="2026-04-02", ctx=mcp_context)

    request = _last_touch_request(client)
    assert request["RelativeSize"] == [str(_BROAD_RELATIVE_SIZE)]
    assert request["TradeLevelRank"] == [str(_BROAD_RANK)]
    assert float(request["MinDollars"][0]) == _BROAD_MIN_DOLLARS


def test_ticker_filter_defaults(
    sample_trade_level_touch_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Apply permissive filter defaults when tickers are specified."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _serve_touches(client, sample_trade_level_touch_response)

    trade_level_touches_tool(tickers="AAPL", date="2026-04-02", ctx=mcp_context)

    request = _last_touch_request(client)
    assert request["RelativeSize"] == ["0"]
    assert request["TradeLevelRank"] == [str(_TICKER_RANK)]
    assert float(request["MinDollars"][0]) == _TICKER_MIN_DOLLARS


def test_explicit_filters_win(
    sample_trade_level_touch_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Pass explicit filters through instead of applying defaults."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _serve_touches(client, sample_trade_level_touch_response)

    trade_level_touches_tool(
        date="2026-04-02",
        relative_size=_EXPLICIT_RELATIVE_SIZE,
        trade_level_rank=_EXPLICIT_RANK,
        min_dollars=_EXPLICIT_MIN_DOLLARS,
        ctx=mcp_context,
    )

    request = _last_touch_request(client)
    assert request["RelativeSize"] == [str(_EXPLICIT_RELATIVE_SIZE)]
    assert request["TradeLevelRank"] == [str(_EXPLICIT_RANK)]
    assert float(request["MinDollars"][0]) == _EXPLICIT_MIN_DOLLARS


def test_partial_filter_overrides(
    sample_trade_level_touch_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Mix explicit and default filter values for a ticker query."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _serve_touches(client, sample_trade_level_touch_response)

    trade_level_touches_tool(
        tickers="AAPL",
        date="2026-04-02",
        relative_size=_PARTIAL_RELATIVE_SIZE,
        ctx=mcp_context,
    )

    request = _last_touch_request(client)
    assert request["RelativeSize"] == [str(_PARTIAL_RELATIVE_SIZE)]
    assert request["TradeLevelRank"] == [str(_TICKER_RANK)]
    assert float(request["MinDollars"][0]) == _TICKER_MIN_DOLLARS


def test_default_date_uses_today(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_level_touch_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Use today's date when no date parameter is provided."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _serve_touches(client, sample_trade_level_touch_response)
    monkeypatch.setattr(_tools, "today_date_string", lambda: "2026-04-02")

    trade_level_touches_tool(ctx=mcp_context)

    request = _last_touch_request(client)
    assert request["StartDate"] == ["2026-04-02"]
    assert request["EndDate"] == ["2026-04-02"]


def test_explicit_date_used(
    sample_trade_level_touch_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Use the provided date when explicitly passed."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _serve_touches(client, sample_trade_level_touch_response)

    trade_level_touches_tool(date="2026-03-15", ctx=mcp_context)

    request = _last_touch_request(client)
    assert request["StartDate"] == ["2026-03-15"]
    assert request["EndDate"] == ["2026-03-15"]


def test_endpoint_failure_returns_null_with_warning(
    mcp_context: object,
) -> None:
    """Return touches as null with a warning when endpoint fails."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    client.post_datatables.side_effect = RuntimeError("Server error")

    result = trade_level_touches_tool(date="2026-04-02", ctx=mcp_context)

    assert result["data"]["touches"] is None
    assert any("Failed to fetch trade level touches" in w for w in result["warnings"])


def test_tickers_filter_passed_to_endpoint(
    sample_trade_level_touch_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Pass ticker filter through to the endpoint payload."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _serve_touches(client, sample_trade_level_touch_response)

    trade_level_touches_tool(tickers="AAPL,MSFT", date="2026-04-02", ctx=mcp_context)

    request = _last_touch_request(client)
    assert request["Tickers"] == ["AAPL,MSFT"]


def test_empty_result_returns_empty_list(
    mcp_context: object,
) -> None:
    """Return empty touches list when endpoint returns no rows."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    client.post_datatables.return_value = []

    result = trade_level_touches_tool(date="2026-04-02", ctx=mcp_context)

    assert result["data"]["touches"] == []
    assert result["metadata"]["touch_count"] == 0
    assert result["metadata"]["total_available"] == 0


def test_metadata_counts(
    sample_trade_level_touch_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Include accurate count and total_available metadata."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _serve_touches(client, sample_trade_level_touch_response)

    result = trade_level_touches_tool(date="2026-04-02", ctx=mcp_context)

    assert result["metadata"]["touch_count"] == 1
    # TotalRows from fixture is 1705.
    assert result["metadata"]["total_available"] == _TOTAL_AVAILABLE


def test_metadata_null_on_failure(
    mcp_context: object,
) -> None:
    """Return null metadata when endpoint fails."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    client.post_datatables.side_effect = RuntimeError("Timeout")

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
        """In-memory client serving the real trade level touch payload."""

        def post_datatables(self, _path: str, _body: str) -> list[dict[str, Any]]:
            """Serve the trade level touches DataTables payload."""
            return sample_trade_level_touch_response["data"]

        def close(self) -> None:
            """Provide the close method expected by lifespan cleanup."""

    monkeypatch.setattr(_mcp_utils, "VolumeLeadersClient", _FakeClient)

    async with Client(_mcp_module.mcp) as client:
        result = await client.call_tool(
            "trade_level_touches",
            {"date": "2026-04-02"},
        )

    assert result.data is not None
    assert result.data["data"]["touches"] is not None
