"""Tests for the sector_themes MCP tool."""

from __future__ import annotations

from importlib import import_module
from typing import Any

_exceptions = import_module("volumeleaders._exceptions")
_tools = import_module("volumeleaders.mcp.tools.sector_themes")
_models = import_module("volumeleaders.models")

APIError = _exceptions.APIError
sector_themes_tool = _tools.sector_themes
SectorThemeNotional = _models.SectorThemeNotional

_TOP_LIMIT = 2


def test_sector_themes_success(
    mcp_context: object,
    sample_sector_themes_response: list[dict[str, Any]],
) -> None:
    """Validate sector_themes produces hierarchical tree of sectors and themes."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    client.post_json.return_value = sample_sector_themes_response

    result = sector_themes_tool(
        date="2026-08-19",
        sector="Technology",
        top_themes=_TOP_LIMIT,
        top_tickers=_TOP_LIMIT,
        include_query=True,
        ctx=mcp_context,  # type: ignore[arg-type]
    )

    assert "data" in result
    assert "metadata" in result
    assert "query" in result
    assert len(result["data"]) == 1
    tech = result["data"][0]
    assert tech["sector"] == "Technology"
    assert len(tech["themes"]) <= _TOP_LIMIT
    first_theme = tech["themes"][0]
    assert "theme" in first_theme
    assert "tickers" in first_theme
    assert len(first_theme["tickers"]) <= _TOP_LIMIT


def test_sector_themes_filter_theme(
    mcp_context: object,
    sample_sector_themes_response: list[dict[str, Any]],
) -> None:
    """Validate sector_themes filters by theme slug or name."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    client.post_json.return_value = sample_sector_themes_response

    result = sector_themes_tool(
        theme="enterprise-software",
        ctx=mcp_context,  # type: ignore[arg-type]
    )

    assert len(result["data"]) > 0
    for s in result["data"]:
        for t in s["themes"]:
            assert "enterprise software" in t["theme"].casefold()


def test_sector_themes_api_error(
    mcp_context: object,
) -> None:
    """Validate error handling on API failure."""
    client = mcp_context.lifespan_context.client  # type: ignore[attr-defined]
    client.post_json.side_effect = APIError("Timeout", status_code=504)

    result = sector_themes_tool(ctx=mcp_context)  # type: ignore[arg-type]
    assert result["data"] == []
    assert "warnings" in result
