"""MCP tool for statistical institutional volume outliers."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any

from fastmcp.dependencies import CurrentContext
from pydantic import Field

from volumeleaders._exceptions import APIError
from volumeleaders.endpoints.sector import get_institutional_outliers
from volumeleaders.mcp import mcp
from volumeleaders.mcp.utils import (
    capture_non_auth_error,
    count_rows,
    format_date,
    format_dollars,
    resolve_client,
    today_date_string,
)

_DEFAULT_CONTEXT = CurrentContext()

if TYPE_CHECKING:
    from fastmcp import Context

    from volumeleaders._client import VolumeLeadersClient
    from volumeleaders.models import InstitutionalOutlier


def _parse_filter_set(filter_str: str) -> set[str]:
    """Parse a comma-separated filter string into a case-folded set."""
    if not filter_str.strip():
        return set()
    return {s.strip().casefold() for s in filter_str.split(",") if s.strip()}


def _curate_outlier(outlier: InstitutionalOutlier) -> dict[str, Any]:
    """Curate a single institutional outlier record for MCP consumption."""
    return {
        "ticker": outlier.ticker,
        "date": format_date(outlier.date),
        "sector": outlier.sector,
        "industry": outlier.industry,
        "sigmas": round(outlier.sigmas, 1),
        "dollars": format_dollars(outlier.dollars),
        "price": outlier.price,
        "trades": outlier.trade_count,
        "trade_rank": outlier.trade_rank,
    }


def _fetch_outliers(
    client: VolumeLeadersClient,
    query_date: str,
    lookback_days: int,
    min_sigmas: float,
    warnings: list[str],
) -> list[InstitutionalOutlier]:
    """Fetch raw outlier rows with error capture."""
    try:
        return get_institutional_outliers(
            client,
            end_date=query_date,
            lookback_days=lookback_days,
            min_std=min_sigmas,
        )
    except APIError as error:
        capture_non_auth_error(warnings, "Failed to fetch institutional outliers", error)
        return []


def _filter_and_sort_outliers(
    rows: list[InstitutionalOutlier],
    ticker_set: set[str],
    sector_set: set[str],
) -> list[InstitutionalOutlier]:
    """Filter rows by tickers/sectors and sort descending by sigmas."""
    filtered = [
        r
        for r in rows
        if (not ticker_set or r.ticker.casefold() in ticker_set)
        and (not sector_set or r.sector.casefold() in sector_set)
    ]
    filtered.sort(key=lambda x: x.sigmas, reverse=True)
    return filtered


@mcp.tool
def institutional_outliers(
    date: Annotated[
        str,
        Field(
            description="Query date in YYYY-MM-DD format. Defaults to today.",
        ),
    ] = "",
    lookback_days: Annotated[
        int,
        Field(
            description=(
                "Historical lookback window in days for baseline volume calculation. "
                "Defaults to 7."
            ),
        ),
    ] = 7,
    min_sigmas: Annotated[
        float,
        Field(
            description=(
                "Minimum standard deviations above historical average (Z-score). "
                "Defaults to 2.0."
            ),
        ),
    ] = 2.0,
    tickers: Annotated[
        str,
        Field(
            description=(
                "Comma-separated ticker symbols to filter (e.g. 'AAPL,NVDA'). "
                "Empty string returns all tickers."
            ),
        ),
    ] = "",
    sectors: Annotated[
        str,
        Field(
            description=(
                "Comma-separated sector names to filter (e.g. 'Technology,Financial Services'). "
                "Empty string returns all sectors."
            ),
        ),
    ] = "",
    max_results: Annotated[
        int,
        Field(
            description="Maximum number of outlier records to return. Defaults to 25.",
        ),
    ] = 25,
    include_query: Annotated[
        bool,
        Field(
            description="Include resolved query parameters in response.",
        ),
    ] = False,
    ctx: Context = _DEFAULT_CONTEXT,
) -> dict[str, Any]:
    """Scan for institutional block trade volume anomalies exceeding statistical thresholds."""
    client = resolve_client(ctx)
    resolved_date = date or today_date_string()
    warnings: list[str] = []

    raw_rows = _fetch_outliers(
        client,
        resolved_date,
        lookback_days,
        min_sigmas,
        warnings,
    )
    ticker_set = _parse_filter_set(tickers)
    sector_set = _parse_filter_set(sectors)

    filtered = _filter_and_sort_outliers(raw_rows, ticker_set, sector_set)
    total_matching = len(filtered)
    curated = [_curate_outlier(r) for r in filtered[:max_results]]

    envelope: dict[str, Any] = {
        "data": curated,
        "metadata": {
            "returned_records": count_rows(curated),
            "total_matching": total_matching,
            "lookback_days": lookback_days,
            "min_sigmas": min_sigmas,
            "date": resolved_date,
        },
    }

    if include_query:
        envelope["query"] = {
            "date": resolved_date,
            "lookback_days": lookback_days,
            "min_sigmas": min_sigmas,
            "tickers": tickers,
            "sectors": sectors,
            "max_results": max_results,
        }

    if warnings:
        envelope["warnings"] = warnings

    return envelope
