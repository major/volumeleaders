"""Tests for the sector_rotation_rrg MCP tool."""

from __future__ import annotations

from importlib import import_module
from typing import Any
from unittest.mock import Mock

from volumeleaders._exceptions import APIError

_tools = import_module("volumeleaders.mcp.tools.sector_rotation_rrg")
_models = import_module("volumeleaders.models")

sector_rotation_rrg_tool = _tools.sector_rotation_rrg
SectorDailyReturn = _models.SectorDailyReturn


def test_sector_rotation_rrg_success(
    mcp_context: Any,
    sample_sector_daily_returns_response: list[dict[str, Any]],
) -> None:
    """Validate sector_rotation_rrg computes JdK RRG quadrants and trails."""
    client = mcp_context.lifespan_context.client
    client.post_form.return_value = sample_sector_daily_returns_response

    result = sector_rotation_rrg_tool(
        window=20,
        roc_period=5,
        trail_length=3,
        equity_only=True,
        include_query=True,
        ctx=mcp_context,
    )

    assert "data" in result
    assert "metadata" in result
    assert "query" in result
    assert len(result["data"]) > 0
    first = result["data"][0]
    assert "sector" in first
    assert "quadrant" in first
    assert first["quadrant"] in {"Leading", "Weakening", "Lagging", "Improving"}
    assert "rs_ratio" in first
    assert "rs_momentum" in first
    assert "trajectory" in first
    assert "trail" in first
    assert len(first["trail"]) <= 3


def test_sector_rotation_rrg_filter_sectors(
    mcp_context: Any,
    sample_sector_daily_returns_response: list[dict[str, Any]],
) -> None:
    """Validate sector_rotation_rrg filters by sector names."""
    client = mcp_context.lifespan_context.client
    client.post_form.return_value = sample_sector_daily_returns_response

    result = sector_rotation_rrg_tool(
        sectors="Technology,Energy",
        equity_only=False,
        ctx=mcp_context,
    )

    sectors_returned = {r["sector"] for r in result["data"]}
    assert sectors_returned.issubset({"Technology", "Energy"})


def test_sector_rotation_rrg_error_handling(
    mcp_context: Any,
) -> None:
    """Validate error handling on API failure."""
    client = mcp_context.lifespan_context.client
    client.post_form.side_effect = APIError("Service error", status_code=500)

    result = sector_rotation_rrg_tool(ctx=mcp_context)
    assert result["data"] == []
    assert "warnings" in result
