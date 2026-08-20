"""Tests for the institutional_outliers MCP tool."""

from __future__ import annotations

from importlib import import_module
from typing import Any
from unittest.mock import Mock

from volumeleaders._exceptions import APIError

_tools = import_module("volumeleaders.mcp.tools.institutional_outliers")
_models = import_module("volumeleaders.models")

institutional_outliers_tool = _tools.institutional_outliers
InstitutionalOutlier = _models.InstitutionalOutlier


def test_institutional_outliers_success(
    mcp_context: Any,
    sample_institutional_outliers_response: list[dict[str, Any]],
) -> None:
    """Validate institutional_outliers returns curated anomaly records."""
    client = mcp_context.lifespan_context.client
    client.post_json.return_value = sample_institutional_outliers_response

    result = institutional_outliers_tool(
        date="2026-08-19",
        lookback_days=7,
        min_sigmas=2.0,
        max_results=10,
        include_query=True,
        ctx=mcp_context,
    )

    assert "data" in result
    assert "metadata" in result
    assert "query" in result
    assert len(result["data"]) == 10
    first = result["data"][0]
    assert first["ticker"] == "VCIT"
    assert first["sigmas"] == 132.5
    assert first["dollars"] == "$865.4M"
    assert result["metadata"]["returned_records"] == 10


def test_institutional_outliers_filter_ticker_sector(
    mcp_context: Any,
    sample_institutional_outliers_response: list[dict[str, Any]],
) -> None:
    """Validate institutional_outliers filters by ticker and sector."""
    client = mcp_context.lifespan_context.client
    client.post_json.return_value = sample_institutional_outliers_response

    result = institutional_outliers_tool(
        tickers="VCIT,SCHO",
        sectors="Bonds",
        ctx=mcp_context,
    )

    for item in result["data"]:
        assert item["ticker"] in {"VCIT", "SCHO"}
        assert item["sector"] == "Bonds"


def test_institutional_outliers_error_handling(
    mcp_context: Any,
) -> None:
    """Validate error handling on API failure."""
    client = mcp_context.lifespan_context.client
    client.post_json.side_effect = APIError("Service down", status_code=503)

    result = institutional_outliers_tool(ctx=mcp_context)
    assert result["data"] == []
    assert "warnings" in result
