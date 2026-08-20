"""MCP tool for sector institutional dollar volume flows."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any

from fastmcp.dependencies import CurrentContext
from pydantic import Field

from volumeleaders._exceptions import APIError
from volumeleaders.endpoints.sector import get_sector_breakdown
from volumeleaders.mcp import mcp
from volumeleaders.mcp.utils import (
    capture_non_auth_error,
    count_rows,
    format_datekey_to_iso,
    format_dollars,
    one_week_ago_date_string,
    resolve_client,
    today_date_string,
)

_DEFAULT_CONTEXT = CurrentContext()

if TYPE_CHECKING:
    from fastmcp import Context

    from volumeleaders._client import VolumeLeadersClient
    from volumeleaders.models import SectorBreakdown


def _parse_filter_set(filter_str: str) -> set[str]:
    """Parse a comma-separated filter string into a case-folded set."""
    if not filter_str.strip():
        return set()
    return {s.strip().casefold() for s in filter_str.split(",") if s.strip()}


def _curate_sector_flow(
    item: SectorBreakdown,
    daily_total: float,
) -> dict[str, Any]:
    """Curate a single sector breakdown record for MCP consumption."""
    share_pct = round((item.dollars / daily_total) * 100, 1) if daily_total > 0 else 0.0
    return {
        "date": format_datekey_to_iso(item.date_key),
        "sector": item.sector,
        "dollars": format_dollars(item.dollars),
        "market_share_pct": share_pct,
    }


def _fetch_sector_flows(
    client: VolumeLeadersClient,
    start_date: str,
    end_date: str,
    warnings: list[str],
) -> list[SectorBreakdown]:
    """Fetch raw sector breakdown rows with error capture."""
    try:
        return get_sector_breakdown(
            client,
            start_date=start_date,
            end_date=end_date,
        )
    except APIError as error:
        capture_non_auth_error(warnings, "Failed to fetch sector flows", error)
        return []


def _compute_daily_totals(rows: list[SectorBreakdown]) -> dict[int, float]:
    """Sum total dollar volume per date key across all sectors."""
    totals: dict[int, float] = {}
    for r in rows:
        totals[r.date_key] = totals.get(r.date_key, 0.0) + r.dollars
    return totals


@mcp.tool
def sector_flows(
    start_date: Annotated[
        str,
        Field(
            description=(
                "Start date in YYYY-MM-DD format. Defaults to one week ago."
            ),
        ),
    ] = "",
    end_date: Annotated[
        str,
        Field(
            description="End date in YYYY-MM-DD format. Defaults to today.",
        ),
    ] = "",
    sectors: Annotated[
        str,
        Field(
            description=(
                "Comma-separated sector names to filter (e.g. 'Technology,Energy'). "
                "Empty string returns all sectors."
            ),
        ),
    ] = "",
    include_query: Annotated[
        bool,
        Field(
            description="Include resolved query parameters in response.",
        ),
    ] = False,
    ctx: Context = _DEFAULT_CONTEXT,
) -> dict[str, Any]:
    """Scan institutional dollar volume flows and market share allocation across sectors."""
    client = resolve_client(ctx)
    resolved_start = start_date or one_week_ago_date_string()
    resolved_end = end_date or today_date_string()
    warnings: list[str] = []

    raw_rows = _fetch_sector_flows(
        client,
        resolved_start,
        resolved_end,
        warnings,
    )
    daily_totals = _compute_daily_totals(raw_rows)
    sector_set = _parse_filter_set(sectors)

    curated = [
        _curate_sector_flow(r, daily_totals.get(r.date_key, 0.0))
        for r in raw_rows
        if not sector_set or r.sector.casefold() in sector_set
    ]

    envelope: dict[str, Any] = {
        "data": curated,
        "metadata": {
            "records_count": count_rows(curated),
            "dates_count": len({row["date"] for row in curated}),
            "sectors_count": len({row["sector"] for row in curated}),
            "start_date": resolved_start,
            "end_date": resolved_end,
        },
    }

    if include_query:
        envelope["query"] = {
            "start_date": resolved_start,
            "end_date": resolved_end,
            "sectors": sectors,
        }

    if warnings:
        envelope["warnings"] = warnings

    return envelope
