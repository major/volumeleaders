"""Tests for the trade_clusters MCP tool."""

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
_tools = import_module("volumeleaders.mcp.tools.trade_clusters")

APIError = _exceptions.APIError
trade_clusters_tool = _tools.trade_clusters

_RESULT_COUNT = 1
_TOTAL_AVAILABLE = 2
_MAX_RESULTS = 7
_CLUSTER_PRICE = 655.1
_SNAPSHOT_PRICE = 655.2
_EXPLICIT_DATE = "2026-03-15"
_TRADE_COUNT = 29
_RANK = 9999
_DOLLARS_MULTIPLIER = 7.12
_CUMULATIVE_DISTRIBUTION = 0.9701


def _form_body(client: Mock) -> dict[str, list[str]]:
    """Decode the DataTables form body from the last endpoint call."""
    _, body = client.post_datatables.call_args.args
    return parse_qs(body)


def test_trade_clusters_success(
    mcp_context: object,
    sample_trade_cluster_response: dict[str, Any],
) -> None:
    """Validate the envelope shape and curated cluster fields."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    client.post_datatables.return_value = sample_trade_cluster_response["data"]

    result = trade_clusters_tool(date="2026-04-01", ctx=mcp_context)  # type: ignore[arg-type]

    assert set(result) == {"data", "metadata"}
    assert set(result["data"]) == {"clusters"}
    assert set(result["metadata"]) == {"cluster_count", "total_available"}
    assert result["metadata"]["cluster_count"] == _RESULT_COUNT
    # TotalRows from the fixture is 2.
    assert result["metadata"]["total_available"] == _TOTAL_AVAILABLE

    cluster = result["data"]["clusters"][0]
    assert set(cluster) == {
        "ticker",
        "sector",
        "industry",
        "time_range",
        "trade_count",
        "current_price",
        "cluster_price",
        "dollars",
        "volume",
        "rank",
        "dollars_multiplier",
        "cumulative_distribution",
        "last_comparable_date",
    }
    assert cluster["ticker"] == "SPY"
    assert cluster["sector"] == "Large Caps"
    assert cluster["time_range"] == "10:28 - 17:55"
    assert cluster["trade_count"] == _TRADE_COUNT
    assert cluster["cluster_price"] == _CLUSTER_PRICE
    assert cluster["dollars"] == "$2.2B"
    assert cluster["rank"] == _RANK
    assert cluster["dollars_multiplier"] == _DOLLARS_MULTIPLIER
    assert cluster["cumulative_distribution"] == _CUMULATIVE_DISTRIBUTION
    assert cluster["last_comparable_date"] == "2026-03-31"
    # No snapshot was primed, so no live price is available.
    assert cluster["current_price"] is None


def test_trade_clusters_ticker_filter_passed(
    mcp_context: object,
    sample_trade_cluster_response: dict[str, Any],
) -> None:
    """Pass the ticker filter through to the DataTables request body."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    client.post_datatables.return_value = sample_trade_cluster_response["data"]

    trade_clusters_tool(tickers="SPY", date="2026-04-01", ctx=mcp_context)  # type: ignore[arg-type]

    assert _form_body(client)["Tickers"] == ["SPY"]


@pytest.mark.parametrize(
    ("date_arg", "expected_date"),
    [
        ("", "2026-04-01"),
        (_EXPLICIT_DATE, _EXPLICIT_DATE),
    ],
)
def test_trade_clusters_date_filter(
    monkeypatch: pytest.MonkeyPatch,
    mcp_context: object,
    sample_trade_cluster_response: dict[str, Any],
    date_arg: str,
    expected_date: str,
) -> None:
    """Default to today and honor an explicit date for both range bounds."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    client.post_datatables.return_value = sample_trade_cluster_response["data"]
    monkeypatch.setattr(_tools, "today_date_string", lambda: "2026-04-01")

    trade_clusters_tool(date=date_arg, ctx=mcp_context)  # type: ignore[arg-type]

    body = _form_body(client)
    assert body["StartDate"] == [expected_date]
    assert body["EndDate"] == [expected_date]


def test_trade_clusters_api_error_warning(
    mcp_context: object,
) -> None:
    """Capture a non-auth API error as a warning with null data."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    client.post_datatables.side_effect = APIError("Backend timeout", status_code=500)

    result = trade_clusters_tool(date="2026-04-01", ctx=mcp_context)  # type: ignore[arg-type]

    assert result["data"]["clusters"] is None
    assert result["metadata"] == {"cluster_count": None, "total_available": None}
    assert any("Failed to fetch trade clusters" in w for w in result["warnings"])


def test_trade_clusters_snapshots_enrich_current_price(
    mcp_context: object,
    sample_trade_cluster_response: dict[str, Any],
    sample_snapshot_string: str,
) -> None:
    """Populate current_price from the snapshot lookup."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    client.post_datatables.return_value = sample_trade_cluster_response["data"]
    client.post_json.return_value = json.loads(sample_snapshot_string)

    result = trade_clusters_tool(date="2026-04-01", ctx=mcp_context)  # type: ignore[arg-type]

    assert result["data"]["clusters"][0]["current_price"] == _SNAPSHOT_PRICE
    assert "warnings" not in result


def test_trade_clusters_snapshot_failure_warns_and_nulls_price(
    mcp_context: object,
    sample_trade_cluster_response: dict[str, Any],
) -> None:
    """Keep cluster data but null current_price when snapshots fail."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    client.post_datatables.return_value = sample_trade_cluster_response["data"]
    client.post_json.side_effect = APIError("Snapshots down", status_code=500)

    result = trade_clusters_tool(date="2026-04-01", ctx=mcp_context)  # type: ignore[arg-type]

    assert result["data"]["clusters"][0]["current_price"] is None
    assert result["metadata"]["cluster_count"] == _RESULT_COUNT
    assert any("Failed to fetch snapshot prices" in w for w in result["warnings"])


def test_trade_clusters_max_results_passed(
    mcp_context: object,
    sample_trade_cluster_response: dict[str, Any],
) -> None:
    """Pass max_results through as the DataTables length parameter."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    client.post_datatables.return_value = sample_trade_cluster_response["data"]

    trade_clusters_tool(
        date="2026-04-01",
        max_results=_MAX_RESULTS,
        ctx=mcp_context,  # type: ignore[arg-type]
    )

    assert _form_body(client)["length"] == [str(_MAX_RESULTS)]


@pytest.mark.asyncio
async def test_fastmcp_client_transport(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_cluster_response: dict[str, Any],
    sample_snapshot_string: str,
) -> None:
    """Call the registered tool through FastMCP client transport."""

    class _FakeClient:
        """Test client object used for lifespan initialization."""

        def __init__(self) -> None:
            """Return fixture payloads for endpoint and snapshot calls."""
            self.post_datatables = Mock(
                return_value=sample_trade_cluster_response["data"],
            )
            self.post_json = Mock(return_value=json.loads(sample_snapshot_string))

        def close(self) -> None:
            """Provide the close method expected by lifespan cleanup."""

    monkeypatch.setattr(_mcp_utils, "VolumeLeadersClient", _FakeClient)

    async with Client(_mcp_module.mcp) as client:
        result = await client.call_tool("trade_clusters", {"date": "2026-04-01"})

    assert result.data is not None
    assert result.data["data"]["clusters"] is not None
    assert result.data["data"]["clusters"][0]["current_price"] == _SNAPSHOT_PRICE
