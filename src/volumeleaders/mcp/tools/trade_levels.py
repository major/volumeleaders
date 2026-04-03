"""MCP tool for trade level data."""

from __future__ import annotations

from typing import Annotated, Any

from fastmcp import Context
from fastmcp.dependencies import CurrentContext
from pydantic import Field

from volumeleaders.endpoints.chart import get_company
from volumeleaders.endpoints.levels import get_trade_levels
from volumeleaders.endpoints.trades import get_all_snapshots
from volumeleaders.mcp import mcp
from volumeleaders.mcp.utils import (
    capture_non_auth_error,
    count_rows,
    format_date,
    format_dollars,
    one_year_ago_date_string,
    resolve_client,
    today_date_string,
)
from volumeleaders.models import TradeLevel


def _curate_level(level: TradeLevel) -> dict[str, Any]:
    """Return compact trade level fields for MCP consumption.

    Field definitions:
      price: The institutional trade level price point.
      dollars: Formatted total dollar volume at this level ("$166.5M",
        "$1.2B"). Reflects accumulated institutional block trade
        activity at this price.
      volume: Total share volume at this level.
      trades: Number of institutional block trades composing this level.
      rank: Significance rank of the level for this ticker (1 = largest
        by dollar volume, 0 = unranked).
      relative_size: This level's dollar volume as a proportion of the
        ticker's total institutional volume across all levels (0.0-1.0).
        Higher = more concentrated institutional activity at this price.
      cumulative_distribution: Cumulative share of total institutional
        dollar volume up to and including this level (0.0-1.0).
      level_origin_date: When the first institutional trade at this
        level occurred (earliest block trade in the cluster).
      level_last_confirmed: When the most recent institutional trade
        at this level occurred (latest block trade in the cluster).
      proximity_pct: Distance from current price as a percentage.
        Positive = level is above current price, negative = below.
        Added after curation when current price is available.
    """
    return {
        "price": level.price,
        "dollars": format_dollars(level.dollars),
        "volume": level.volume,
        "trades": level.trades,
        "rank": level.trade_level_rank,
        "relative_size": level.relative_size,
        "cumulative_distribution": level.cumulative_distribution,
        "level_origin_date": format_date(level.min_date),
        "level_last_confirmed": format_date(level.max_date),
    }


def _get_current_price(client: Any, ticker: str, warnings: list[str]) -> float | None:
    """Resolve current price using the best available API source.

    `GetCompany` is the cheapest lookup, but the real API often returns
    `CurrentPrice: null`. When that happens, fall back to `GetAllSnapshots`,
    which carries the live ticker-price map used elsewhere in the project.
    Warnings are only emitted when both sources fail due to actual errors.
    """
    company_error: Exception | None = None
    snapshot_error: Exception | None = None

    try:
        company = get_company(client, ticker=ticker)
    except Exception as error:
        company_error = error
    else:
        if company.current_price is not None:
            return company.current_price

    try:
        snapshots = get_all_snapshots(client)
    except Exception as error:
        snapshot_error = error
    else:
        return snapshots.get(ticker)

    if company_error is not None:
        capture_non_auth_error(
            warnings,
            "Failed to fetch current price from company metadata",
            company_error,
        )
    if snapshot_error is not None:
        capture_non_auth_error(
            warnings, "Failed to fetch current price from snapshots", snapshot_error
        )
    return None


@mcp.tool
def trade_levels(
    ticker: Annotated[
        str,
        Field(
            description=(
                "Ticker symbol to look up trade levels for "
                "(e.g. 'AAPL', 'AMD'). Required."
            ),
        ),
    ],
    start_date: Annotated[
        str,
        Field(
            description=(
                "Start of the lookback window in YYYY-MM-DD format. "
                "Trade levels are computed from block trades within "
                "this window. Defaults to one year ago."
            ),
        ),
    ] = "",
    end_date: Annotated[
        str,
        Field(
            description=(
                "End of the lookback window in YYYY-MM-DD format. Defaults to today."
            ),
        ),
    ] = "",
    min_dollars: Annotated[
        float,
        Field(
            ge=0,
            description="Minimum dollar value filter for levels. Defaults to $500K.",
        ),
    ] = 500_000,
    relative_size: Annotated[
        int,
        Field(
            ge=0,
            le=100,
            description=(
                "Minimum relative size filter (0-100). Relative size "
                "measures this level's dollar volume as a share of the "
                "ticker's total institutional volume. "
                "Defaults to 0 (no filter)."
            ),
        ),
    ] = 0,
    trade_level_rank: Annotated[
        int,
        Field(
            ge=-1,
            le=100,
            description=(
                "Maximum trade level rank filter. Only levels ranked "
                "at or above this threshold are returned. "
                "-1 = no filter. Defaults to -1."
            ),
        ),
    ] = -1,
    trade_level_count: Annotated[
        int,
        Field(
            ge=1,
            le=100,
            description=(
                "How many trade levels the server should compute "
                "for this ticker. Defaults to 10."
            ),
        ),
    ] = 10,
    ctx: Context = CurrentContext(),
) -> dict[str, Any]:
    """Look up institutional trade levels for a ticker.

    A **trade level** is a price where institutional block trades have
    accumulated over time, forming a support/resistance zone backed by
    real money. Levels are created when multiple block trades cluster
    near the same price (server-determined tolerance). Each level is
    ranked by total dollar volume (rank 1 = largest).

    Use this tool when you need to know **where** institutional money
    is concentrated for a specific stock or ETF. The levels represent
    prices where large block trades have historically occurred,
    indicating significant institutional interest.

    Key fields per level:
    - rank: significance of the level (1 = largest by dollars,
      0 = unranked)
    - relative_size: level's share of the ticker's total institutional
      volume (0.0-1.0, higher = more concentrated)
    - dollars: formatted total institutional dollars at this level
    - cumulative_distribution: running total of institutional volume
      share across all levels (0.0-1.0)
    - level_origin_date / level_last_confirmed: date range of the
      block trades composing this level
    """
    eff_start = start_date if start_date else one_year_ago_date_string()
    eff_end = end_date if end_date else today_date_string()
    warnings: list[str] = []
    client = resolve_client(ctx)

    levels_data: list[dict[str, Any]] | None = None
    try:
        raw_levels = get_trade_levels(
            client,
            ticker=ticker,
            start_date=eff_start,
            end_date=eff_end,
            min_dollars=min_dollars,
            relative_size=relative_size,
            trade_level_rank=trade_level_rank,
            trade_level_count=trade_level_count,
        )
        levels_data = [_curate_level(level) for level in raw_levels]
    except Exception as error:
        capture_non_auth_error(warnings, "Failed to fetch trade levels", error)

    current_price = _get_current_price(client, ticker, warnings)

    # Enrich levels with proximity to current price.
    if levels_data is not None and current_price:
        for level in levels_data:
            level["proximity_pct"] = round(
                (level["price"] - current_price) / current_price * 100, 2
            )

    result: dict[str, Any] = {}
    result["data"] = {"levels": levels_data}
    if warnings:
        result["warnings"] = warnings
    result["metadata"] = {
        "level_count": count_rows(levels_data),
        "current_price": current_price,
    }
    return result
