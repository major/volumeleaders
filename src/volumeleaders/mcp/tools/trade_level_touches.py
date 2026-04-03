"""MCP tool for trade level touch events."""

from __future__ import annotations

from typing import Annotated, Any

from fastmcp import Context
from fastmcp.dependencies import CurrentContext
from pydantic import Field

from volumeleaders.endpoints.levels import get_trade_level_touches
from volumeleaders.mcp import mcp
from volumeleaders.mcp.utils import (
    capture_non_auth_error,
    count_rows,
    format_date,
    format_dollars,
    resolve_client,
    today_date_string,
)
from volumeleaders.models import TradeLevelTouch


# Per-ticker defaults: permissive filters for single-ticker lookups.
_TICKER_RELATIVE_SIZE = 0
_TICKER_TRADE_LEVEL_RANK = 10
_TICKER_MIN_DOLLARS: float = 500_000

# Broad-scan defaults: tighter filters when scanning all tickers.
_BROAD_RELATIVE_SIZE = 5
_BROAD_TRADE_LEVEL_RANK = 5
_BROAD_MIN_DOLLARS: float = 500_000_000


def _resolve_filters(
    *,
    tickers: str,
    relative_size: int | None,
    trade_level_rank: int | None,
    min_dollars: float | None,
) -> tuple[int, int, float]:
    """Pick filter defaults based on query scope.

    Single-ticker queries use permissive defaults to surface more data.
    Broad scans (no tickers) use tighter defaults to keep results
    manageable.  Explicit caller values always win.
    """
    if tickers:
        return (
            relative_size if relative_size is not None else _TICKER_RELATIVE_SIZE,
            trade_level_rank
            if trade_level_rank is not None
            else _TICKER_TRADE_LEVEL_RANK,
            min_dollars if min_dollars is not None else _TICKER_MIN_DOLLARS,
        )
    return (
        relative_size if relative_size is not None else _BROAD_RELATIVE_SIZE,
        trade_level_rank if trade_level_rank is not None else _BROAD_TRADE_LEVEL_RANK,
        min_dollars if min_dollars is not None else _BROAD_MIN_DOLLARS,
    )


def _format_time(touch: TradeLevelTouch) -> str:
    """Extract compact HH:MM time from the touch timestamp.

    Prefers the 24-hour time string when available, falling back
    to parsing the full datetime string.
    """
    if touch.full_time_string24:
        return touch.full_time_string24[:5]
    # Fallback: parse from "2026-04-01 : 17:51:00"
    parts = touch.full_date_time.split(" : ", maxsplit=1)
    return parts[1][:5] if len(parts) == 2 else touch.full_date_time


def _curate_touch(touch: TradeLevelTouch) -> dict[str, Any]:
    """Return compact trade level touch fields for MCP consumption.

    Field definitions:
      ticker: Symbol of the stock/ETF being touched.
      time: When the touch occurred (HH:MM, 24-hour format).
      price: The institutional trade level price being revisited.
      dollars: Formatted dollar volume of the level ("$11.4B",
        "$478.1M"). Reflects accumulated institutional activity at
        this price, not just today's touch.
      volume: Share volume at this level.
      trades: Number of institutional block trades composing this level.
      rank: Significance rank of the level for this ticker (1 = largest
        by dollar volume). Only the top N levels are tracked.
      relative_size: This level's dollar volume as a proportion of the
        ticker's total institutional volume across all levels (0.0-1.0).
        Higher = more concentrated institutional activity at this price.
      level_origin_date: When the first institutional trade at this
        level occurred (earliest block trade in the cluster).
      level_last_confirmed: When the most recent institutional trade
        at this level occurred (latest block trade, not price revisit).
    """
    return {
        "ticker": touch.ticker,
        "time": _format_time(touch),
        "price": touch.price,
        "dollars": format_dollars(touch.dollars),
        "volume": touch.volume,
        "trades": touch.trades,
        "rank": touch.trade_level_rank,
        "relative_size": touch.relative_size,
        "level_origin_date": format_date(touch.min_date),
        "level_last_confirmed": format_date(touch.max_date),
    }


@mcp.tool
def trade_level_touches(
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
            description="Date to query in YYYY-MM-DD format. Defaults to today.",
        ),
    ] = "",
    relative_size: Annotated[
        int | None,
        Field(
            ge=0,
            le=100,
            description=(
                "Minimum relative size filter (0-100). Relative size "
                "measures this level's dollar volume as a share of the "
                "ticker's total institutional volume. "
                "Defaults to 0 for ticker queries, 5 for broad scans."
            ),
        ),
    ] = None,
    trade_level_rank: Annotated[
        int | None,
        Field(
            ge=1,
            le=100,
            description=(
                "Maximum trade level rank filter (1 = largest level by "
                "dollar volume). Only levels ranked at or above this "
                "threshold are returned. "
                "Defaults to 10 for ticker queries, 5 for broad scans."
            ),
        ),
    ] = None,
    min_dollars: Annotated[
        float | None,
        Field(
            ge=0,
            description=(
                "Minimum dollar value filter. "
                "Set to 0 to include small-cap tickers. "
                "Defaults to $500K for ticker queries, $500M for broad scans."
            ),
        ),
    ] = None,
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
    """Find trade level touch events for a given day.

    A **trade level** is a price where institutional block trades have
    accumulated over time, forming a support/resistance zone backed by
    real money. Levels are created when multiple block trades cluster
    near the same price (server-determined tolerance). Each level is
    ranked by total dollar volume (rank 1 = largest).

    A **trade level touch** is an intraday event where price revisits
    one of these institutional levels. Touches signal that price is
    re-engaging a zone where institutions previously committed capital,
    which often produces support/resistance reactions.

    Key fields per touch:
    - rank: significance of the level (1 = largest by dollars)
    - relative_size: level's share of the ticker's total institutional
      volume (0.0-1.0, higher = more concentrated)
    - dollars: formatted total institutional dollars at this level
    - level_origin_date / level_last_confirmed: date range of the
      block trades composing this level (not price revisits)
    """
    query_date = date if date else today_date_string()
    eff_rs, eff_tlr, eff_md = _resolve_filters(
        tickers=tickers,
        relative_size=relative_size,
        trade_level_rank=trade_level_rank,
        min_dollars=min_dollars,
    )
    warnings: list[str] = []
    client = resolve_client(ctx)

    touches_data: list[dict[str, Any]] | None = None
    total_count: int | None = None
    try:
        raw_touches = get_trade_level_touches(
            client,
            tickers=tickers,
            start_date=query_date,
            end_date=query_date,
            relative_size=eff_rs,
            trade_level_rank=eff_tlr,
            min_dollars=eff_md,
            length=max_results,
        )
        touches_data = [_curate_touch(t) for t in raw_touches]
        total_count = raw_touches[0].total_rows if raw_touches else 0
    except Exception as error:
        capture_non_auth_error(warnings, "Failed to fetch trade level touches", error)

    result: dict[str, Any] = {}
    result["data"] = {"touches": touches_data}
    if warnings:
        result["warnings"] = warnings
    result["metadata"] = {
        "touch_count": count_rows(touches_data),
        "total_available": total_count,
    }
    return result
