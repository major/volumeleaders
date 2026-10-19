"""Tests for the trade_levels MCP tool."""

from __future__ import annotations

from importlib import import_module
from typing import Any

import pytest
from fastmcp import Client

_mcp_module = import_module("volumeleaders.mcp")
_mcp_utils = import_module("volumeleaders.mcp.utils")
_tools = import_module("volumeleaders.mcp.tools.trade_levels")

trade_levels_tool = _tools.trade_levels

_LEVEL_COUNT = 3
_CURRENT_PRICE = 209.95
_FIRST_LEVEL_PRICE = 36.8
_FIRST_LEVEL_VOLUME = 39671

_FAKE_CURRENT_PRICE = 23.50


# -- Tool integration tests ----------------------------------------------------


def _company_payload(
    sample_company_response: dict[str, Any],
    *,
    current_price: float | None,
) -> dict[str, Any]:
    """Return the real company fixture with a chosen current price."""
    return {**sample_company_response, "CurrentPrice": current_price}


def _wire_post_json(
    client: object,
    *,
    sample_company_response: dict[str, Any],
    levels: list[dict[str, Any]] | None = None,
    levels_error: Exception | None = None,
    company_price: float | None = None,
    company_error: Exception | None = None,
    snapshots: str = "",
    snapshots_error: Exception | None = None,
) -> None:
    """Route chart endpoint calls to real payloads or configured errors."""
    company = _company_payload(sample_company_response, current_price=company_price)

    def fake_post_json(path: str, _payload: dict[str, Any]) -> object:
        """Serve one of the three chart endpoints used by the tool."""
        if path == "/Chart0/GetChartTradeLevels":
            if levels_error is not None:
                raise levels_error
            return levels or []
        if path == "/Chart0/GetCompany":
            if company_error is not None:
                raise company_error
            return company
        if path == "/Trades/GetAllSnapshots":
            if snapshots_error is not None:
                raise snapshots_error
            return snapshots
        msg = f"Unexpected endpoint: {path}"
        raise AssertionError(msg)

    client.post_json.side_effect = fake_post_json


def _level_request(client: object) -> dict[str, Any]:
    """Return the payload from the latest GetChartTradeLevels call."""
    for call in client.post_json.call_args_list:
        if call.args[0] == "/Chart0/GetChartTradeLevels":
            return call.args[1]
    msg = "GetChartTradeLevels was not called"
    raise AssertionError(msg)


def test_envelope_shape_default(
    sample_chart_trade_levels_response: list[dict[str, Any]],
    sample_company_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Return minimal envelope by default: data and metadata only."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _wire_post_json(
        client,
        sample_company_response=sample_company_response,
        levels=sample_chart_trade_levels_response,
        company_price=_FAKE_CURRENT_PRICE,
    )

    result = trade_levels_tool(ticker="AMD", end_date="2026-04-02", ctx=mcp_context)

    # No warnings when endpoint succeeds.
    assert set(result) == {"data", "metadata"}
    assert set(result["data"]) == {"levels"}
    assert set(result["metadata"]) == {"level_count", "current_price"}


def test_envelope_omits_warnings_when_empty(
    sample_chart_trade_levels_response: list[dict[str, Any]],
    sample_company_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Omit the warnings key entirely when there are no warnings."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _wire_post_json(
        client,
        sample_company_response=sample_company_response,
        levels=sample_chart_trade_levels_response,
        company_price=_FAKE_CURRENT_PRICE,
    )

    result = trade_levels_tool(ticker="AMD", end_date="2026-04-02", ctx=mcp_context)

    assert "warnings" not in result


def test_envelope_includes_warnings_when_present(
    sample_company_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Include warnings key when endpoint fails."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _wire_post_json(
        client,
        sample_company_response=sample_company_response,
        levels_error=RuntimeError("Server error"),
        company_price=_FAKE_CURRENT_PRICE,
    )

    result = trade_levels_tool(ticker="AMD", end_date="2026-04-02", ctx=mcp_context)

    assert "warnings" in result
    assert any("Failed to fetch trade levels" in w for w in result["warnings"])


def test_curated_fields_in_response(
    sample_chart_trade_levels_response: list[dict[str, Any]],
    sample_company_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Curate level rows to the expected compact field set in tool response."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _wire_post_json(
        client,
        sample_company_response=sample_company_response,
        levels=sample_chart_trade_levels_response,
        company_price=_FAKE_CURRENT_PRICE,
    )

    result = trade_levels_tool(ticker="AMD", end_date="2026-04-02", ctx=mcp_context)

    assert result["data"]["levels"] is not None
    assert len(result["data"]["levels"]) == _LEVEL_COUNT
    assert set(result["data"]["levels"][0]) == {
        "price",
        "dollars",
        "volume",
        "trades",
        "rank",
        "relative_size",
        "cumulative_distribution",
        "level_origin_date",
        "level_last_confirmed",
        "proximity_pct",
    }


def test_curated_values_in_response(
    sample_chart_trade_levels_response: list[dict[str, Any]],
    sample_company_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Map model attributes to curated level values in the response."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _wire_post_json(
        client,
        sample_company_response=sample_company_response,
        levels=sample_chart_trade_levels_response,
        company_price=_FAKE_CURRENT_PRICE,
    )

    result = trade_levels_tool(ticker="AMD", end_date="2026-04-02", ctx=mcp_context)

    level = result["data"]["levels"][0]
    assert level["price"] == _FIRST_LEVEL_PRICE
    assert level["dollars"] == "$1.5M"
    assert level["volume"] == _FIRST_LEVEL_VOLUME
    assert level["trades"] == 1
    assert level["rank"] == 1
    # The chart endpoint omits these optional fields; they stay null.
    assert level["relative_size"] is None
    assert level["cumulative_distribution"] is None
    assert level["level_origin_date"] == "2026-05-19"
    assert level["level_last_confirmed"] is None


def test_default_dates(
    monkeypatch: pytest.MonkeyPatch,
    sample_chart_trade_levels_response: list[dict[str, Any]],
    sample_company_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Default end_date to today and start_date to five years ago."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _wire_post_json(
        client,
        sample_company_response=sample_company_response,
        levels=sample_chart_trade_levels_response,
        company_price=_FAKE_CURRENT_PRICE,
    )
    monkeypatch.setattr(_tools, "today_date_string", lambda: "2026-04-02")
    monkeypatch.setattr(_tools, "five_years_ago_date_string", lambda: "2021-04-02")

    trade_levels_tool(ticker="AMD", ctx=mcp_context)

    request = _level_request(client)
    assert request["StartDateKey"] == "20210402"
    assert request["EndDateKey"] == "20260402"


def test_explicit_dates_used(
    sample_chart_trade_levels_response: list[dict[str, Any]],
    sample_company_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Use explicit dates when provided."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _wire_post_json(
        client,
        sample_company_response=sample_company_response,
        levels=sample_chart_trade_levels_response,
        company_price=_FAKE_CURRENT_PRICE,
    )

    trade_levels_tool(
        ticker="AMD",
        start_date="2025-01-01",
        end_date="2026-03-15",
        ctx=mcp_context,
    )

    request = _level_request(client)
    assert request["StartDateKey"] == "20250101"
    assert request["EndDateKey"] == "20260315"


def test_ticker_passed_to_endpoint(
    sample_chart_trade_levels_response: list[dict[str, Any]],
    sample_company_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Pass ticker through to the endpoint payload."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _wire_post_json(
        client,
        sample_company_response=sample_company_response,
        levels=sample_chart_trade_levels_response,
        company_price=_FAKE_CURRENT_PRICE,
    )

    trade_levels_tool(ticker="AMD", end_date="2026-04-02", ctx=mcp_context)

    request = _level_request(client)
    assert request["Ticker"] == "AMD"


def test_dates_passed_to_endpoint(
    sample_chart_trade_levels_response: list[dict[str, Any]],
    sample_company_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Pass start_date and end_date through to the endpoint payload."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _wire_post_json(
        client,
        sample_company_response=sample_company_response,
        levels=sample_chart_trade_levels_response,
        company_price=_FAKE_CURRENT_PRICE,
    )

    trade_levels_tool(
        ticker="AMD",
        start_date="2025-04-02",
        end_date="2026-04-02",
        ctx=mcp_context,
    )

    request = _level_request(client)
    assert request["StartDateKey"] == "20250402"
    assert request["EndDateKey"] == "20260402"


def test_endpoint_failure_returns_null_with_warning(
    sample_company_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Return levels as null with a warning when endpoint fails."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _wire_post_json(
        client,
        sample_company_response=sample_company_response,
        levels_error=RuntimeError("Server error"),
        company_price=_FAKE_CURRENT_PRICE,
    )

    result = trade_levels_tool(ticker="AMD", end_date="2026-04-02", ctx=mcp_context)

    assert result["data"]["levels"] is None
    assert any("Failed to fetch trade levels" in w for w in result["warnings"])


def test_empty_result_returns_empty_list(
    sample_company_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Return empty levels list when endpoint returns no rows."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _wire_post_json(
        client,
        sample_company_response=sample_company_response,
        levels=[],
        company_price=_FAKE_CURRENT_PRICE,
    )

    result = trade_levels_tool(ticker="AMD", end_date="2026-04-02", ctx=mcp_context)

    assert result["data"]["levels"] == []
    assert result["metadata"]["level_count"] == 0


def test_metadata_counts(
    sample_chart_trade_levels_response: list[dict[str, Any]],
    sample_company_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Include accurate level count in metadata."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _wire_post_json(
        client,
        sample_company_response=sample_company_response,
        levels=sample_chart_trade_levels_response,
        company_price=_FAKE_CURRENT_PRICE,
    )

    result = trade_levels_tool(ticker="AMD", end_date="2026-04-02", ctx=mcp_context)

    assert result["metadata"]["level_count"] == _LEVEL_COUNT


def test_metadata_null_on_failure(
    sample_company_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Return null metadata when endpoint fails."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _wire_post_json(
        client,
        sample_company_response=sample_company_response,
        levels_error=RuntimeError("Timeout"),
        company_price=_FAKE_CURRENT_PRICE,
    )

    result = trade_levels_tool(ticker="AMD", end_date="2026-04-02", ctx=mcp_context)

    assert result["metadata"]["level_count"] is None


def test_proximity_pct_computed_from_current_price(
    sample_chart_trade_levels_response: list[dict[str, Any]],
    sample_company_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Enrich levels with proximity_pct relative to current price."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _wire_post_json(
        client,
        sample_company_response=sample_company_response,
        levels=sample_chart_trade_levels_response,
        company_price=_FAKE_CURRENT_PRICE,
    )

    result = trade_levels_tool(ticker="AMD", end_date="2026-04-02", ctx=mcp_context)

    first_level = result["data"]["levels"][0]
    assert "proximity_pct" in first_level
    # Compare against the same proximity calculation used by the tool.
    expected = round(
        (first_level["price"] - _FAKE_CURRENT_PRICE) / _FAKE_CURRENT_PRICE * 100,
        2,
    )
    assert first_level["proximity_pct"] == expected


def test_proximity_pct_absent_when_no_current_price(
    sample_chart_trade_levels_response: list[dict[str, Any]],
    sample_company_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Omit proximity_pct when all current price sources fail."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _wire_post_json(
        client,
        sample_company_response=sample_company_response,
        levels=sample_chart_trade_levels_response,
        company_error=RuntimeError("Company lookup failed"),
        snapshots_error=RuntimeError("Snapshot lookup failed"),
    )

    result = trade_levels_tool(ticker="AMD", end_date="2026-04-02", ctx=mcp_context)

    assert "proximity_pct" not in result["data"]["levels"][0]


def test_metadata_includes_current_price(
    sample_chart_trade_levels_response: list[dict[str, Any]],
    sample_company_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Include the ticker's current price in metadata."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _wire_post_json(
        client,
        sample_company_response=sample_company_response,
        levels=sample_chart_trade_levels_response,
        company_price=_FAKE_CURRENT_PRICE,
    )

    result = trade_levels_tool(ticker="AMD", end_date="2026-04-02", ctx=mcp_context)

    assert result["metadata"]["current_price"] == _FAKE_CURRENT_PRICE


def test_metadata_falls_back_to_snapshots_when_company_price_null(
    sample_chart_trade_levels_response: list[dict[str, Any]],
    sample_company_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Populate metadata current_price from snapshots when company price is null."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _wire_post_json(
        client,
        sample_company_response=sample_company_response,
        levels=sample_chart_trade_levels_response,
        company_price=None,
        snapshots=f"AMD:{_CURRENT_PRICE}",
    )

    result = trade_levels_tool(ticker="AMD", end_date="2026-04-02", ctx=mcp_context)

    assert result["metadata"]["current_price"] == _CURRENT_PRICE
    # A null company price is not an error; snapshots recover it silently.
    assert "warnings" not in result


def test_current_price_failure_warns(
    sample_chart_trade_levels_response: list[dict[str, Any]],
    sample_company_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Warn and return null current_price when both lookup paths fail."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _wire_post_json(
        client,
        sample_company_response=sample_company_response,
        levels=sample_chart_trade_levels_response,
        company_error=RuntimeError("Company lookup failed"),
        snapshots_error=RuntimeError("Snapshot lookup failed"),
    )

    result = trade_levels_tool(ticker="AMD", end_date="2026-04-02", ctx=mcp_context)

    assert result["metadata"]["current_price"] is None
    assert any(
        "Failed to fetch current price from company metadata" in w
        for w in result["warnings"]
    )
    assert any(
        "Failed to fetch current price from snapshots" in w for w in result["warnings"]
    )
    # Levels should still be returned even if current price fails.
    assert result["data"]["levels"] is not None
    assert len(result["data"]["levels"]) == _LEVEL_COUNT


def test_current_price_company_failure_uses_snapshots_without_warning(
    sample_chart_trade_levels_response: list[dict[str, Any]],
    sample_company_response: dict[str, Any],
    mcp_context: object,
) -> None:
    """Recover current price from snapshots when company lookup raises."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    _wire_post_json(
        client,
        sample_company_response=sample_company_response,
        levels=sample_chart_trade_levels_response,
        company_error=RuntimeError("Company lookup failed"),
        snapshots=f"AMD:{_CURRENT_PRICE}",
    )

    result = trade_levels_tool(ticker="AMD", end_date="2026-04-02", ctx=mcp_context)

    assert result["metadata"]["current_price"] == _CURRENT_PRICE
    assert "warnings" not in result


@pytest.mark.asyncio
async def test_fastmcp_client_transport(
    monkeypatch: pytest.MonkeyPatch,
    sample_chart_trade_levels_response: list[dict[str, Any]],
    sample_company_response: dict[str, Any],
) -> None:
    """Call the registered tool through FastMCP client transport."""

    class _FakeClient:
        """In-memory client serving the real chart endpoint payloads."""

        def post_json(self, path: str, _payload: dict[str, Any]) -> object:
            """Serve the chart endpoints used by the trade_levels tool."""
            if path == "/Chart0/GetChartTradeLevels":
                return sample_chart_trade_levels_response
            if path == "/Chart0/GetCompany":
                return _company_payload(
                    sample_company_response,
                    current_price=_FAKE_CURRENT_PRICE,
                )
            if path == "/Trades/GetAllSnapshots":
                return ""
            msg = f"Unexpected endpoint: {path}"
            raise AssertionError(msg)

        def close(self) -> None:
            """Provide the close method expected by lifespan cleanup."""

    monkeypatch.setattr(_mcp_utils, "VolumeLeadersClient", _FakeClient)

    async with Client(_mcp_module.mcp) as client:
        result = await client.call_tool(
            "trade_levels",
            {"ticker": "AMD", "end_date": "2026-04-02"},
        )

    assert result.data is not None
    assert result.data["data"]["levels"] is not None
