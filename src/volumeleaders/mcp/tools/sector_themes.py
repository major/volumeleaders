"""MCP tool for hierarchical sector, theme, and ticker capital flows."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any

from fastmcp.dependencies import CurrentContext
from pydantic import Field

from volumeleaders._exceptions import APIError
from volumeleaders.endpoints.sector import get_notional_by_sector_by_name
from volumeleaders.mcp import mcp
from volumeleaders.mcp.utils import (
    capture_non_auth_error,
    format_dollars,
    resolve_client,
    today_date_string,
)

_DEFAULT_CONTEXT = CurrentContext()

if TYPE_CHECKING:
    from fastmcp import Context

    from volumeleaders._client import VolumeLeadersClient
    from volumeleaders.models import SectorThemeNotional


def _group_sector_themes(
    rows: list[SectorThemeNotional],
    top_themes: int,
    top_tickers: int,
) -> list[dict[str, Any]]:
    """Group flat notional records into a compact hierarchical tree."""
    sectors_map: dict[str, dict[str, Any]] = {}

    for r in rows:
        if r.sector not in sectors_map:
            sectors_map[r.sector] = {
                "sector": r.sector,
                "rank": r.sector_rank,
                "themes_map": {},
            }

        s_entry = sectors_map[r.sector]
        t_map = s_entry["themes_map"]

        if r.theme not in t_map:
            t_map[r.theme] = {
                "theme": r.theme,
                "rank": r.theme_rank,
                "share_of_sector_pct": round(r.theme_pct_of_sector, 1),
                "tickers": [],
            }

        t_entry = t_map[r.theme]
        t_entry["tickers"].append(
            {
                "ticker": r.ticker,
                "dollars": format_dollars(r.dollars),
                "share_of_theme_pct": round(r.ticker_pct_of_theme, 1),
                "trades": r.trades,
            },
        )

    curated_sectors: list[dict[str, Any]] = []
    for s_name, s_data in sorted(sectors_map.items(), key=lambda x: x[1]["rank"]):
        themes_list = list(s_data["themes_map"].values())
        themes_list.sort(key=lambda t: t["rank"])
        capped_themes = themes_list[:top_themes]

        for t in capped_themes:
            t["tickers"] = t["tickers"][:top_tickers]

        curated_sectors.append(
            {
                "sector": s_name,
                "rank": s_data["rank"],
                "themes": capped_themes,
            },
        )

    return curated_sectors


def _fetch_sector_themes(
    client: VolumeLeadersClient,
    query_date: str,
    warnings: list[str],
) -> list[SectorThemeNotional]:
    """Fetch raw sector theme notional rows with error capture."""
    try:
        return get_notional_by_sector_by_name(
            client,
            end_date=query_date,
            top_themes=10,
            top_tickers=10,
        )
    except APIError as error:
        capture_non_auth_error(warnings, "Failed to fetch sector theme notional", error)
        return []


def _filter_theme_rows(
    rows: list[SectorThemeNotional],
    sector: str,
    theme: str,
) -> list[SectorThemeNotional]:
    """Filter rows matching sector and theme keywords."""
    target_sector = sector.strip().casefold()
    target_theme = theme.strip().casefold()
    return [
        r
        for r in rows
        if (not target_sector or target_sector in r.sector.casefold())
        and (
            not target_theme
            or target_theme in r.theme.casefold()
            or target_theme in r.theme_slug.casefold()
        )
    ]


@mcp.tool
def sector_themes(  # noqa: PLR0913
    date: Annotated[
        str,
        Field(
            description="Query date in YYYY-MM-DD format. Defaults to today.",
        ),
    ] = "",
    sector: Annotated[
        str,
        Field(
            description=(
                "Target sector name to filter (e.g. 'Technology', 'Healthcare'). "
                "Empty string returns all sectors."
            ),
        ),
    ] = "",
    theme: Annotated[
        str,
        Field(
            description=(
                "Target theme name or slug to filter (e.g. 'enterprise-software'). "
                "Empty string returns all themes."
            ),
        ),
    ] = "",
    top_themes: Annotated[
        int,
        Field(
            description="Number of top themes per sector (1-10). Defaults to 3.",
        ),
    ] = 3,
    top_tickers: Annotated[
        int,
        Field(
            description="Number of top tickers per theme (1-10). Defaults to 3.",
        ),
    ] = 3,
    include_query: Annotated[  # noqa: FBT002
        bool,
        Field(
            description="Include resolved query parameters in response.",
        ),
    ] = False,
    ctx: Context = _DEFAULT_CONTEXT,
) -> dict[str, Any]:
    """Examine hierarchical capital flows across sectors, themes, and tickers."""
    client = resolve_client(ctx)
    resolved_date = date or today_date_string()
    warnings: list[str] = []

    raw_rows = _fetch_sector_themes(client, resolved_date, warnings)
    filtered = _filter_theme_rows(raw_rows, sector, theme)

    grouped = _group_sector_themes(
        filtered,
        top_themes=max(1, min(10, top_themes)),
        top_tickers=max(1, min(10, top_tickers)),
    )

    envelope: dict[str, Any] = {
        "data": grouped,
        "metadata": {
            "sectors_count": len(grouped),
            "date": resolved_date,
            "top_themes_limit": top_themes,
            "top_tickers_limit": top_tickers,
        },
    }

    if include_query:
        envelope["query"] = {
            "date": resolved_date,
            "sector": sector,
            "theme": theme,
            "top_themes": top_themes,
            "top_tickers": top_tickers,
        }

    if warnings:
        envelope["warnings"] = warnings

    return envelope
