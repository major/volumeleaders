"""MCP tool for trade cluster data."""

from __future__ import annotations

from typing import Annotated, Any

from fastmcp import Context
from fastmcp.dependencies import CurrentContext
from pydantic import Field

from volumeleaders.endpoints.trades import get_trade_clusters
from volumeleaders.mcp import mcp
from volumeleaders.mcp.utils import (
    capture_non_auth_error,
    count_rows,
    fetch_snapshot_prices,
    format_date,
    format_dollars,
    resolve_client,
    today_date_string,
)
from volumeleaders.models import TradeCluster


def _format_time_range(cluster: TradeCluster) -> str:
    """Format min/max time strings into a compact range.

    Returns "HH:MM - HH:MM" using the 24-hour time strings
    from the cluster's time window.
    """
    start = cluster.min_full_time_string24[:5]
    end = cluster.max_full_time_string24[:5]
    return f"{start} - {end}"


def _curate_cluster(
    cluster: TradeCluster,
    snapshots: dict[str, float],
) -> dict[str, Any]:
    """Return compact trade cluster fields for MCP consumption.

    Field definitions:
      ticker: Symbol of the stock/ETF.
      sector: Market sector of the security.
      industry: Market industry of the security.
      time_range: Window of clustered trades ("HH:MM - HH:MM").
      trade_count: Number of institutional block trades in this cluster.
      current_price: Live price from snapshot data. None when
        snapshot lookup fails.
      cluster_price: Price at which the cluster formed.
      dollars: Formatted total dollar volume of the cluster ("$5.8M",
        "$2.2B"). Reflects accumulated institutional block trade value.
      volume: Total share volume in the cluster.
      rank: Significance rank (1 = largest by dollar volume,
        9999 = unranked).
      dollars_multiplier: This cluster's dollar volume relative to
        typical institutional activity. Higher = more unusual.
      cumulative_distribution: Cumulative percentile of institutional
        dollar volume (0.0-1.0). Values near 1.0 mean this cluster
        is among the largest seen.
      last_comparable_date: When a similar-sized cluster last occurred
        for this ticker. None if no prior comparable cluster exists.
    """
    return {
        "ticker": cluster.ticker,
        "sector": cluster.sector,
        "industry": cluster.industry,
        "time_range": _format_time_range(cluster),
        "trade_count": cluster.trade_count,
        "current_price": snapshots.get(cluster.ticker),
        "cluster_price": cluster.price,
        "dollars": format_dollars(cluster.dollars),
        "volume": cluster.volume,
        "rank": cluster.trade_cluster_rank,
        "dollars_multiplier": round(cluster.dollars_multiplier, 2),
        "cumulative_distribution": cluster.cumulative_distribution,
        "last_comparable_date": format_date(cluster.last_comparible_trade_cluster_date),
    }


@mcp.tool
def trade_clusters(
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
    date: Annotated[
        str,
        Field(
            description=(
                "Date to query in YYYY-MM-DD format. "
                "Used as both start and end date. Defaults to today."
            ),
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
    """Find institutional trade clusters for a given day.

    A **trade cluster** is a group of institutional block trades in the
    same security that occur within a time window on a single day.
    Clusters indicate concentrated institutional activity, where
    multiple large block trades converge on the same stock in a short
    period, suggesting coordinated or conviction-driven positioning.

    Key fields per cluster:
    - rank: significance of the cluster (1 = largest by dollars,
      9999 = unranked)
    - dollars_multiplier: how unusual this cluster's size is relative
      to typical institutional activity (higher = more unusual)
    - cumulative_distribution: percentile of institutional dollar
      volume (values near 1.0 = among the largest clusters)
    - last_comparable_date: when a similar-sized cluster last occurred
    """
    query_date = date if date else today_date_string()
    warnings: list[str] = []
    client = resolve_client(ctx)

    clusters_data: list[dict[str, Any]] | None = None
    total_count: int | None = None
    try:
        raw_clusters = get_trade_clusters(
            client,
            tickers=tickers,
            start_date=query_date,
            end_date=query_date,
            length=max_results,
        )
        snapshots = fetch_snapshot_prices(client, warnings=warnings)
        clusters_data = [_curate_cluster(c, snapshots) for c in raw_clusters]
        total_count = raw_clusters[0].total_rows if raw_clusters else 0
    except Exception as error:
        capture_non_auth_error(warnings, "Failed to fetch trade clusters", error)

    result: dict[str, Any] = {}
    result["data"] = {"clusters": clusters_data}
    if warnings:
        result["warnings"] = warnings
    result["metadata"] = {
        "cluster_count": count_rows(clusters_data),
        "total_available": total_count,
    }
    return result
