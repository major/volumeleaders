"""Tests for the sector_factors MCP tool."""

from __future__ import annotations

from importlib import import_module
from typing import Any
from unittest.mock import Mock

from volumeleaders._exceptions import APIError

_tools = import_module("volumeleaders.mcp.tools.sector_factors")
_models = import_module("volumeleaders.models")

sector_factors_tool = _tools.sector_factors
SectorDailyReturn = _models.SectorDailyReturn


def test_sector_factors_success_all_metrics(
    mcp_context: Any,
    sample_sector_daily_returns_response: list[dict[str, Any]],
) -> None:
    """Validate sector_factors returns full scorecard for latest date."""
    client = mcp_context.lifespan_context.client
    client.post_form.return_value = sample_sector_daily_returns_response

    result = sector_factors_tool(
        timeframe="blended",
        metric="all",
        include_query=True,
        ctx=mcp_context,
    )

    assert "data" in result
    assert "metadata" in result
    assert "query" in result
    assert len(result["data"]) > 0
    first = result["data"][0]
    assert "sector" in first
    assert "momentum_pct" in first
    assert "relative_strength_pct" in first
    assert "sharpe" in first
    assert "beta" in first
    assert "realized_vol_pct" in first
    assert result["metadata"]["benchmark"] == "SPY"


def test_sector_factors_single_metric_filter(
    mcp_context: Any,
    sample_sector_daily_returns_response: list[dict[str, Any]],
) -> None:
    """Validate sector_factors filters to a specific metric."""
    client = mcp_context.lifespan_context.client
    client.post_form.return_value = sample_sector_daily_returns_response

    result = sector_factors_tool(
        metric="momentum",
        timeframe="10d",
        ctx=mcp_context,
    )

    first = result["data"][0]
    assert "momentum_pct" in first
    assert "sharpe" not in first


def test_sector_factors_filter_sectors(
    mcp_context: Any,
    sample_sector_daily_returns_response: list[dict[str, Any]],
) -> None:
    """Validate sector_factors filters by sector names."""
    client = mcp_context.lifespan_context.client
    client.post_form.return_value = sample_sector_daily_returns_response

    result = sector_factors_tool(
        sectors="Technology,Bonds",
        ctx=mcp_context,
    )

    for item in result["data"]:
        assert item["sector"] in {"Technology", "Bonds"}


def test_sector_factors_error_handling(
    mcp_context: Any,
) -> None:
    """Validate error handling on API failure."""
    client = mcp_context.lifespan_context.client
    client.post_form.side_effect = APIError("Timeout", status_code=504)

    result = sector_factors_tool(ctx=mcp_context)
    assert result["data"] == []
    assert "warnings" in result
