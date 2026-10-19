"""Tests for the trade_cluster_bombs MCP tool."""

from __future__ import annotations

import json
from importlib import import_module
from typing import Any
from unittest.mock import Mock
from urllib.parse import parse_qs

import pytest
from fastmcp import Client

_exceptions = import_module("volumeleaders._exceptions")
_mcp_module = import_module("volumeleaders.mcp")
_mcp_utils = import_module("volumeleaders.mcp.utils")
_tools = import_module("volumeleaders.mcp.tools.trade_cluster_bombs")

APIError = _exceptions.APIError
trade_cluster_bombs_tool = _tools.trade_cluster_bombs

_RESULT_COUNT = 1
_TOTAL_AVAILABLE = 1
_MAX_RESULTS = 7
_SNAPSHOT_PRICE = 155.08
_WEEK_AGO = "2026-03-26"
_TODAY = "2026-04-02"


def _form_body(client: Mock) -> dict[str, list[str]]:
    """Decode the DataTables form body from the last endpoint call."""
    _, body = client.post_datatables.call_args.args
    return parse_qs(body)


def test_trade_cluster_bombs_success(
    mcp_context: object,
    sample_trade_cluster_bomb_response: dict[str, Any],
) -> None:
    """Validate the envelope shape and curated bomb fields."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    client.post_datatables.return_value = sample_trade_cluster_bomb_response["data"]

    result = trade_cluster_bombs_tool(  # type: ignore[arg-type]
        start_date="2026-04-02",
        end_date="2026-04-02",
        ctx=mcp_context,
    )

    assert set(result) == {"data", "metadata"}
    assert set(result["data"]) == {"bombs"}
    assert set(result["metadata"]) == {"bomb_count", "total_available"}
    assert result["metadata"]["bomb_count"] == _RESULT_COUNT
    # TotalRows from the fixture is 1.
    assert result["metadata"]["total_available"] == _TOTAL_AVAILABLE

    bomb = result["data"]["bombs"][0]
    assert set(bomb) == {
        "ticker",
        "date",
        "time_range",
        "trade_count",
        "sector",
        "industry",
        "current_price",
        "dollars",
        "volume",
        "rank",
        "dollars_multiplier",
        "cumulative_distribution",
        "last_comparable_date",
    }
    assert bomb["ticker"] == "NVS"
    assert bomb["date"] == "2026-04-02"
    assert bomb["time_range"] == "09:41 - 11:27"
    assert bomb["trade_count"] == 8
    assert bomb["sector"] == "Healthcare"
    assert bomb["industry"] == "Pharma"
    assert bomb["dollars"] == "$77.9M"
    assert bomb["volume"] == 506100
    assert bomb["rank"] == 2
    assert bomb["dollars_multiplier"] == 0.75
    assert bomb["cumulative_distribution"] == 0.5
    assert bomb["last_comparable_date"] == "2010-12-15"
    # No snapshot was primed, so no live price is available.
    assert bomb["current_price"] is None


def test_trade_cluster_bombs_ticker_filter_passed(
    mcp_context: object,
    sample_trade_cluster_bomb_response: dict[str, Any],
) -> None:
    """Pass the ticker filter through to the DataTables request body."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    client.post_datatables.return_value = sample_trade_cluster_bomb_response["data"]

    trade_cluster_bombs_tool(  # type: ignore[arg-type]
        tickers="NVS",
        start_date="2026-04-02",
        end_date="2026-04-02",
        ctx=mcp_context,
    )

    assert _form_body(client)["Tickers"] == ["NVS"]


@pytest.mark.parametrize(
    ("start_date_arg", "end_date_arg", "expected_start", "expected_end"),
    [
        ("", "", _WEEK_AGO, _TODAY),
        ("2026-03-01", "2026-03-15", "2026-03-01", "2026-03-15"),
    ],
)
def test_trade_cluster_bombs_date_range(
    monkeypatch: pytest.MonkeyPatch,
    mcp_context: object,
    sample_trade_cluster_bomb_response: dict[str, Any],
    start_date_arg: str,
    end_date_arg: str,
    expected_start: str,
    expected_end: str,
) -> None:
    """Default to a one-week window and honor explicit dates."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    client.post_datatables.return_value = sample_trade_cluster_bomb_response["data"]
    monkeypatch.setattr(_tools, "one_week_ago_date_string", lambda: _WEEK_AGO)
    monkeypatch.setattr(_tools, "today_date_string", lambda: _TODAY)

    trade_cluster_bombs_tool(  # type: ignore[arg-type]
        start_date=start_date_arg,
        end_date=end_date_arg,
        ctx=mcp_context,
    )

    body = _form_body(client)
    assert body["StartDate"] == [expected_start]
    assert body["EndDate"] == [expected_end]


def test_trade_cluster_bombs_api_error_warning(
    mcp_context: object,
) -> None:
    """Capture a non-auth API error as a warning with null data."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    client.post_datatables.side_effect = APIError("Backend timeout", status_code=500)

    result = trade_cluster_bombs_tool(ctx=mcp_context)  # type: ignore[arg-type]

    assert result["data"]["bombs"] is None
    assert result["metadata"] == {"bomb_count": None, "total_available": None}
    assert any("Failed to fetch trade cluster bombs" in w for w in result["warnings"])


def test_trade_cluster_bombs_snapshots_enrich_current_price(
    mcp_context: object,
    sample_trade_cluster_bomb_response: dict[str, Any],
    sample_snapshot_string: str,
) -> None:
    """Populate current_price from the snapshot lookup."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    client.post_datatables.return_value = sample_trade_cluster_bomb_response["data"]
    client.post_json.return_value = json.loads(sample_snapshot_string)

    result = trade_cluster_bombs_tool(  # type: ignore[arg-type]
        start_date="2026-04-02",
        end_date="2026-04-02",
        ctx=mcp_context,
    )

    assert result["data"]["bombs"][0]["current_price"] == _SNAPSHOT_PRICE
    assert "warnings" not in result


def test_trade_cluster_bombs_snapshot_failure_warns_and_nulls_price(
    mcp_context: object,
    sample_trade_cluster_bomb_response: dict[str, Any],
) -> None:
    """Keep bomb data but null current_price when snapshots fail."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    client.post_datatables.return_value = sample_trade_cluster_bomb_response["data"]
    client.post_json.side_effect = APIError("Snapshots down", status_code=500)

    result = trade_cluster_bombs_tool(  # type: ignore[arg-type]
        start_date="2026-04-02",
        end_date="2026-04-02",
        ctx=mcp_context,
    )

    assert result["data"]["bombs"][0]["current_price"] is None
    assert result["metadata"]["bomb_count"] == _RESULT_COUNT
    assert any("Failed to fetch snapshot prices" in w for w in result["warnings"])


def test_trade_cluster_bombs_max_results_passed(
    mcp_context: object,
    sample_trade_cluster_bomb_response: dict[str, Any],
) -> None:
    """Pass max_results through as the DataTables length parameter."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    client.post_datatables.return_value = sample_trade_cluster_bomb_response["data"]

    trade_cluster_bombs_tool(  # type: ignore[arg-type]
        start_date="2026-04-02",
        end_date="2026-04-02",
        max_results=_MAX_RESULTS,
        ctx=mcp_context,
    )

    assert _form_body(client)["length"] == [str(_MAX_RESULTS)]


@pytest.mark.asyncio
async def test_fastmcp_client_transport(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_cluster_bomb_response: dict[str, Any],
    sample_snapshot_string: str,
) -> None:
    """Call the registered tool through FastMCP client transport."""

    class _FakeClient:
        """Test client object used for lifespan initialization."""

        def __init__(self) -> None:
            """Return fixture payloads for endpoint and snapshot calls."""
            self.post_datatables = Mock(
                return_value=sample_trade_cluster_bomb_response["data"],
            )
            self.post_json = Mock(return_value=json.loads(sample_snapshot_string))

        def close(self) -> None:
            """Provide the close method expected by lifespan cleanup."""

    monkeypatch.setattr(_mcp_utils, "VolumeLeadersClient", _FakeClient)

    async with Client(_mcp_module.mcp) as client:
        result = await client.call_tool(
            "trade_cluster_bombs",
            {"start_date": "2026-04-02", "end_date": "2026-04-02"},
        )

    assert result.data is not None
    assert result.data["data"]["bombs"] is not None
    assert result.data["data"]["bombs"][0]["current_price"] == _SNAPSHOT_PRICE
