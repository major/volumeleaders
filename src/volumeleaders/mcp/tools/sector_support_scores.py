"""MCP tool for sector automated supply and demand support scores."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any

from fastmcp.dependencies import CurrentContext
from pydantic import Field

from volumeleaders._exceptions import APIError
from volumeleaders.endpoints.sector import get_supply_demand_areas
from volumeleaders.mcp import mcp
from volumeleaders.mcp.utils import (
    capture_non_auth_error,
    count_rows,
    format_datekey_to_iso,
    one_week_ago_date_string,
    resolve_client,
    today_date_string,
)

_DEFAULT_CONTEXT = CurrentContext()

if TYPE_CHECKING:
    from fastmcp import Context

    from volumeleaders._client import VolumeLeadersClient
    from volumeleaders.models import SupplyDemandArea


def _parse_filter_set(filter_str: str) -> set[str]:
    """Parse a comma-separated filter string into a case-folded set."""
    if not filter_str.strip():
        return set()
    return {s.strip().casefold() for s in filter_str.split(",") if s.strip()}


def _classify_support_bias(median_score: float) -> str:
    """Classify the institutional support bias based on median score."""
    if median_score >= 6.0:
        return "Strong Support"
    if median_score >= 3.0:
        return "Moderate Support"
    return "Supply Overhead"


def _curate_support_area(area: SupplyDemandArea) -> dict[str, Any]:
    """Curate a single sector supply/demand area record for MCP consumption."""
    median = round(area.median_pct_levels_below_latest_close, 1)
    return {
        "sector": area.sector,
        "date": format_datekey_to_iso(area.date_key),
        "ticker_count": area.ticker_count,
        "support_median_pct": median,
        "support_avg_pct": round(area.avg_pct_levels_below_latest_close, 1),
        "support_q1_pct": round(
            area.first_quartile_pct_levels_below_latest_close,
            1,
        ),
        "support_q3_pct": round(
            area.third_quartile_pct_levels_below_latest_close,
            1,
        ),
        "support_range": (
            f"{round(area.min_pct_levels_below_latest_close, 1)}% - "
            f"{round(area.max_pct_levels_below_latest_close, 1)}%"
        ),
        "bias": _classify_support_bias(median),
    }


def _resolve_support_dates(
    date: str,
    start_date: str,
    end_date: str,
) -> tuple[str, str]:
    """Resolve start and end date strings for supply/demand query."""
    if date:
        return date, date
    return start_date or one_week_ago_date_string(), end_date or today_date_string()


def _fetch_support_areas(
    client: VolumeLeadersClient,
    start_date: str,
    end_date: str,
    warnings: list[str],
) -> list[SupplyDemandArea]:
    """Fetch raw supply and demand areas with error capture."""
    try:
        return get_supply_demand_areas(
            client,
            start_date=start_date,
            end_date=end_date,
        )
    except APIError as error:
        capture_non_auth_error(warnings, "Failed to fetch supply demand areas", error)
        return []


def _filter_support_rows(
    raw_rows: list[SupplyDemandArea],
    is_explicit_query: bool,
    sector_set: set[str],
) -> list[SupplyDemandArea]:
    """Slice to latest date when default and filter by sector names."""
    rows = raw_rows
    if not is_explicit_query and rows:
        latest_date_key = max(r.date_key for r in rows)
        rows = [r for r in rows if r.date_key == latest_date_key]

    if not sector_set:
        return rows
    return [r for r in rows if r.sector.casefold() in sector_set]


@mcp.tool
def sector_support_scores(
    date: Annotated[
        str,
        Field(
            description=(
                "Target date in YYYY-MM-DD format. If omitted and start/end dates "
                "are also omitted, returns the latest available date's scores."
            ),
        ),
    ] = "",
    start_date: Annotated[
        str,
        Field(
            description="Start date in YYYY-MM-DD format for multi-day spread history.",
        ),
    ] = "",
    end_date: Annotated[
        str,
        Field(
            description="End date in YYYY-MM-DD format for multi-day spread history.",
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
    """Analyze automated supply and demand support score distributions across sectors."""
    client = resolve_client(ctx)
    resolved_start, resolved_end = _resolve_support_dates(date, start_date, end_date)
    warnings: list[str] = []

    raw_rows = _fetch_support_areas(client, resolved_start, resolved_end, warnings)
    is_explicit = bool(date or start_date or end_date)
    sector_set = _parse_filter_set(sectors)
    filtered = _filter_support_rows(raw_rows, is_explicit, sector_set)

    curated = [_curate_support_area(r) for r in filtered]

    envelope: dict[str, Any] = {
        "data": curated,
        "metadata": {
            "records_count": count_rows(curated),
            "sectors_count": len({r["sector"] for r in curated}),
            "start_date": resolved_start,
            "end_date": resolved_end,
        },
    }

    if include_query:
        envelope["query"] = {
            "date": date,
            "start_date": resolved_start,
            "end_date": resolved_end,
            "sectors": sectors,
        }

    if warnings:
        envelope["warnings"] = warnings

    return envelope
