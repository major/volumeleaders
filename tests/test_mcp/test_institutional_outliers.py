"""Tests for the institutional_outliers MCP tool."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_exceptions = import_module("volumeleaders._exceptions")
_tools = import_module("volumeleaders.mcp.tools.institutional_outliers")
_models = import_module("volumeleaders.models")

APIError = _exceptions.APIError
institutional_outliers_tool = _tools.institutional_outliers
InstitutionalOutlier = _models.InstitutionalOutlier

_EXPECTED_LIMIT = 10
_EXPECTED_SIGMAS = 132.5


def test_institutional_outliers_success(
    mcp_context: object,
    sample_institutional_outliers_response: list[dict[str, Any]],
) -> None:
    """Validate institutional_outliers returns curated anomaly records."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    client.post_json.return_value = sample_institutional_outliers_response

    result = institutional_outliers_tool(
        date="2026-08-19",
        lookback_days=7,
        min_sigmas=2.0,
        max_results=_EXPECTED_LIMIT,
        include_query=True,
        ctx=mcp_context,  # type: ignore[arg-type]
    )

    assert "data" in result
    assert "metadata" in result
    assert "query" in result
    assert len(result["data"]) == _EXPECTED_LIMIT
    first = result["data"][0]
    assert first["ticker"] == "VCIT"
    assert first["sigmas"] == _EXPECTED_SIGMAS
    assert first["dollars"] == "$865.4M"
    assert result["metadata"]["returned_records"] == _EXPECTED_LIMIT


def test_institutional_outliers_filter_ticker_sector(
    mcp_context: object,
    sample_institutional_outliers_response: list[dict[str, Any]],
) -> None:
    """Validate institutional_outliers filters by ticker and sector."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    client.post_json.return_value = sample_institutional_outliers_response

    result = institutional_outliers_tool(
        tickers="VCIT,SCHO",
        sectors="Bonds",
        ctx=mcp_context,  # type: ignore[arg-type]
    )

    for item in result["data"]:
        assert item["ticker"] in {"VCIT", "SCHO"}
        assert item["sector"] == "Bonds"


def test_institutional_outliers_error_handling(
    mcp_context: object,
) -> None:
    """Validate error handling on API failure."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    client.post_json.side_effect = APIError("Service down", status_code=503)

    result = institutional_outliers_tool(ctx=mcp_context)  # type: ignore[arg-type]
    assert result["data"] == []
    assert "warnings" in result
