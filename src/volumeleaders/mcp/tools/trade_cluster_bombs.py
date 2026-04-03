"""MCP tool for trade cluster bomb data."""

from __future__ import annotations

from typing import Annotated, Any

from fastmcp import Context
from fastmcp.dependencies import CurrentContext
from pydantic import Field

from volumeleaders.endpoints.trades import get_trade_cluster_bombs
from volumeleaders.mcp import mcp
from volumeleaders.mcp.utils import (
    capture_non_auth_error,
    count_rows,
    fetch_snapshot_prices,
    format_date,
    format_dollars,
    one_week_ago_date_string,
    resolve_client,
    today_date_string,
)
from volumeleaders.models import TradeClusterBomb


def _format_time_range(bomb: TradeClusterBomb) -> str:
    """Format min/max time strings into a compact range.

    Returns "HH:MM - HH:MM" using the 24-hour time strings
    from the bomb's time window.
    """
    start = bomb.min_full_time_string24[:5]
    end = bomb.max_full_time_string24[:5]
    return f"{start} - {end}"


def _curate_bomb(
    bomb: TradeClusterBomb,
    snapshots: dict[str, float],
) -> dict[str, Any]:
    """Return compact trade cluster bomb fields for MCP consumption.

    Field definitions:
      ticker: Symbol of the stock/ETF.
      date: Trading day when the bomb occurred (YYYY-MM-DD).
      time_range: Window of clustered trades ("HH:MM - HH:MM").
      trade_count: Number of institutional block trades in this bomb.
      sector: Market sector of the security.
      industry: Market industry of the security.
      current_price: Live price from snapshot data. None when
        snapshot lookup fails.
      dollars: Formatted total dollar volume ("$77.9M", "$1.2B").
        Reflects accumulated institutional block trade value.
      volume: Total share volume in the bomb cluster.
      rank: Significance rank (1 = largest by dollar volume,
        2 = second largest, etc.).
      dollars_multiplier: This bomb's dollar volume relative to
        typical institutional activity. Higher = more unusual.
      cumulative_distribution: Cumulative percentile of institutional
        dollar volume (0.0-1.0). Values near 1.0 mean this bomb
        is among the largest seen.
      last_comparable_date: When a comparable cluster bomb last
        occurred for this ticker. None if no prior comparable exists.
    """
    return {
        "ticker": bomb.ticker,
        "date": format_date(bomb.date),
        "time_range": _format_time_range(bomb),
        "trade_count": bomb.trade_count,
        "sector": bomb.sector,
        "industry": bomb.industry,
        "current_price": snapshots.get(bomb.ticker),
        "dollars": format_dollars(bomb.dollars),
        "volume": bomb.volume,
        "rank": bomb.trade_cluster_bomb_rank,
        "dollars_multiplier": round(bomb.dollars_multiplier, 2),
        "cumulative_distribution": bomb.cumulative_distribution,
        "last_comparable_date": format_date(
            bomb.last_comparable_trade_cluster_bomb_date
        ),
    }


@mcp.tool
def trade_cluster_bombs(
    tickers: Annotated[
        str,
        Field(
            description=(
                "Comma-separated ticker symbols to filter "
                "(e.g. 'AAPL' or 'AAPL,MSFT'). "
                "Empty string returns all tickers."
            ),
        ),
    ] = "",
    start_date: Annotated[
        str,
        Field(
            description=("Start date in YYYY-MM-DD format. Defaults to one week ago."),
        ),
    ] = "",
    end_date: Annotated[
        str,
        Field(
            description=("End date in YYYY-MM-DD format. Defaults to today."),
        ),
    ] = "",
    max_results: Annotated[
        int,
        Field(
            ge=1,
            le=500,
            description="Maximum number of results to return.",
        ),
    ] = 50,
    ctx: Context = CurrentContext(),
) -> dict[str, Any]:
    """Find trade cluster bomb events over a date range.

    A **trade cluster bomb** is an exceptionally large trade cluster,
    a rare event where institutional block trades in a single security
    reach an unusually high total dollar volume within a trading day.
    Cluster bombs are significant because they represent extraordinary
    institutional conviction or activity that stands out even among
    normal trade clusters.

    Cluster bombs don't happen every day, so a wider date range
    (default: one week) helps capture recent events.

    Key fields per bomb:
    - rank: significance rank (1 = largest, lower = more significant)
    - dollars_multiplier: how unusual this bomb's size is relative to
      typical institutional activity (higher = more unusual)
    - cumulative_distribution: percentile of institutional dollar
      volume (values near 1.0 = among the largest ever seen)
    - last_comparable_date: when a comparable cluster bomb last
      occurred for this ticker
    """
    eff_start = start_date if start_date else one_week_ago_date_string()
    eff_end = end_date if end_date else today_date_string()
    warnings: list[str] = []
    client = resolve_client(ctx)

    bombs_data: list[dict[str, Any]] | None = None
    total_count: int | None = None
    try:
        raw_bombs = get_trade_cluster_bombs(
            client,
            tickers=tickers,
            start_date=eff_start,
            end_date=eff_end,
            length=max_results,
        )
        snapshots = fetch_snapshot_prices(client, warnings=warnings)
        bombs_data = [_curate_bomb(b, snapshots) for b in raw_bombs]
        total_count = raw_bombs[0].total_rows if raw_bombs else 0
    except Exception as error:
        capture_non_auth_error(warnings, "Failed to fetch trade cluster bombs", error)

    result: dict[str, Any] = {}
    result["data"] = {"bombs": bombs_data}
    if warnings:
        result["warnings"] = warnings
    result["metadata"] = {
        "bomb_count": count_rows(bombs_data),
        "total_available": total_count,
    }
    return result
