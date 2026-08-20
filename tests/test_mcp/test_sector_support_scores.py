"""Tests for the sector_support_scores MCP tool."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_exceptions = import_module("volumeleaders._exceptions")
_tools = import_module("volumeleaders.mcp.tools.sector_support_scores")
_models = import_module("volumeleaders.models")

APIError = _exceptions.APIError
sector_support_scores_tool = _tools.sector_support_scores
SupplyDemandArea = _models.SupplyDemandArea


def test_sector_support_scores_success(
    mcp_context: object,
    sample_supply_demand_areas_response: list[dict[str, Any]],
) -> None:
    """Validate sector_support_scores returns curated statistical summary."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    client.post_json.return_value = sample_supply_demand_areas_response

    result = sector_support_scores_tool(
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
    assert "support_median_pct" in first
    assert "bias" in first


def test_sector_support_scores_latest_date_default(
    mcp_context: object,
    sample_supply_demand_areas_response: list[dict[str, Any]],
) -> None:
    """Validate sector_support_scores defaults to latest date snapshot."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    client.post_json.return_value = sample_supply_demand_areas_response

    result = sector_support_scores_tool(ctx=mcp_context)  # type: ignore[arg-type]
    dates = {r["date"] for r in result["data"]}
    assert len(dates) == 1


def test_sector_support_scores_filter_sectors(
    mcp_context: object,
    sample_supply_demand_areas_response: list[dict[str, Any]],
) -> None:
    """Validate sector_support_scores filters by sector names."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    client.post_json.return_value = sample_supply_demand_areas_response

    result = sector_support_scores_tool(
        sectors="Communication Services",
        ctx=mcp_context,  # type: ignore[arg-type]
    )

    for item in result["data"]:
        assert item["sector"] == "Communication Services"


def test_sector_support_scores_error_handling(
    mcp_context: object,
) -> None:
    """Validate error handling on API failure."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    client.post_json.side_effect = APIError("Server error", status_code=500)

    result = sector_support_scores_tool(ctx=mcp_context)  # type: ignore[arg-type]
    assert result["data"] == []
    assert "warnings" in result
