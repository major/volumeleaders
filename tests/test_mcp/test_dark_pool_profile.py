"""Tests for the dark_pool_profile MCP tool."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_exceptions = import_module("volumeleaders._exceptions")
_tools = import_module("volumeleaders.mcp.tools.dark_pool_profile")
_models = import_module("volumeleaders.models")

APIError = _exceptions.APIError
dark_pool_profile_tool = _tools.dark_pool_profile
DarkPoolVolumeBin = _models.DarkPoolVolumeBin

_EXPECTED_LAST_CLOSE = 317.0
_MAX_NODES = 3


def test_dark_pool_profile_success(
    mcp_context: object,
    sample_dark_pool_volume_report_response: list[dict[str, Any]],
) -> None:
    """Validate dark_pool_profile computes POC and top accumulation nodes."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    client.post_json.return_value = sample_dark_pool_volume_report_response

    result = dark_pool_profile_tool(
        tickers="AAPL",
        start_date="2026-08-12",
        end_date="2026-08-19",
        top_nodes_only=True,
        include_query=True,
        ctx=mcp_context,  # type: ignore[arg-type]
    )

    assert "data" in result
    assert "metadata" in result
    assert "query" in result
    assert len(result["data"]) == 1
    aapl = result["data"][0]
    assert aapl["ticker"] == "AAPL"
    assert aapl["last_close"] == _EXPECTED_LAST_CLOSE
    assert "total_dp_dollars" in aapl
    assert "poc_price_range" in aapl
    assert "poc_dp_dollars" in aapl
    assert "poc_relation" in aapl
    assert "top_accumulation_nodes" in aapl
    assert len(aapl["top_accumulation_nodes"]) <= _MAX_NODES


def test_dark_pool_profile_all_bins(
    mcp_context: object,
    sample_dark_pool_volume_report_response: list[dict[str, Any]],
) -> None:
    """Validate dark_pool_profile returns full bins when top_nodes_only=False."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    client.post_json.return_value = sample_dark_pool_volume_report_response

    result = dark_pool_profile_tool(
        tickers="AAPL",
        top_nodes_only=False,
        ctx=mcp_context,  # type: ignore[arg-type]
    )

    assert len(result["data"]) == 1
    aapl = result["data"][0]
    assert "bins" in aapl
    assert len(aapl["bins"]) > 0


def test_dark_pool_profile_empty_tickers(
    mcp_context: object,
) -> None:
    """Validate empty tickers parameter returns warning."""
    result = dark_pool_profile_tool(
        tickers="",
        ctx=mcp_context,  # type: ignore[arg-type]
    )
    assert result["data"] == []
    assert "warnings" in result


def test_dark_pool_profile_error_handling(
    mcp_context: object,
) -> None:
    """Validate error handling on API failure."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    client.post_json.side_effect = APIError("Backend error", status_code=500)

    result = dark_pool_profile_tool(
        tickers="AAPL",
        ctx=mcp_context,  # type: ignore[arg-type]
    )
    assert result["data"] == []
    assert "warnings" in result
