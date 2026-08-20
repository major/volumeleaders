"""Tests for the sector_flows MCP tool."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_exceptions = import_module("volumeleaders._exceptions")
_tools = import_module("volumeleaders.mcp.tools.sector_flows")
_models = import_module("volumeleaders.models")

APIError = _exceptions.APIError
sector_flows_tool = _tools.sector_flows
SectorBreakdown = _models.SectorBreakdown


def test_sector_flows_success(
    mcp_context: object,
    sample_sector_breakdown_response: list[dict[str, Any]],
) -> None:
    """Validate sector_flows executes successfully and returns curated envelope."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    client.post_json.return_value = sample_sector_breakdown_response

    result = sector_flows_tool(
        start_date="2026-08-12",
        end_date="2026-08-19",
        include_query=True,
        ctx=mcp_context,  # type: ignore[arg-type]
    )

    assert "data" in result
    assert "metadata" in result
    assert "query" in result
    assert len(result["data"]) > 0
    first = result["data"][0]
    assert "sector" in first
    assert "dollars" in first
    assert "market_share_pct" in first
    assert result["metadata"]["start_date"] == "2026-08-12"


def test_sector_flows_filter_sector(
    mcp_context: object,
    sample_sector_breakdown_response: list[dict[str, Any]],
) -> None:
    """Validate sector_flows filters correctly by sector name."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    client.post_json.return_value = sample_sector_breakdown_response

    result = sector_flows_tool(
        sectors="Technology,Bonds",
        ctx=mcp_context,  # type: ignore[arg-type]
    )

    sectors_returned = {r["sector"] for r in result["data"]}
    assert sectors_returned.issubset({"Technology", "Bonds"})


def test_sector_flows_api_error_warning(
    mcp_context: object,
) -> None:
    """Validate sector_flows captures non-auth API error in warnings."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    client.post_json.side_effect = APIError("Backend timeout", status_code=500)

    result = sector_flows_tool(ctx=mcp_context)  # type: ignore[arg-type]
    assert result["data"] == []
    assert "warnings" in result
    assert len(result["warnings"]) > 0
