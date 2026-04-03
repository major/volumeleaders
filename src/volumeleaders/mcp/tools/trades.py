"""MCP tool for institutional block trades."""

from __future__ import annotations

from typing import Annotated, Any

from fastmcp import Context
from fastmcp.dependencies import CurrentContext
from pydantic import Field

from volumeleaders.endpoints.trades import get_trades
from volumeleaders.mcp import mcp
from volumeleaders.mcp.utils import (
    capture_non_auth_error,
    count_rows,
    fetch_snapshot_prices,
    format_date,
    format_dollars,
    ninety_days_ago_date_string,
    normalize_sort_by,
    resolve_client,
    today_date_string,
)
from volumeleaders.models import Trade

# Per-ticker defaults: permissive filters, wider lookback.
_TICKER_INCLUDE_PHANTOM = 1
_TICKER_INCLUDE_OFFSETTING = 1

# Broad-scan defaults: tighter filters, today only.
_BROAD_INCLUDE_PHANTOM = -1
_BROAD_INCLUDE_OFFSETTING = -1

# Maps user-friendly sort names to TRADE_COLUMNS indices and default directions.
# Column indices reference the TRADE_COLUMNS list in endpoints/trades.py.
_SORT_COLUMN_INDEX: dict[str, int] = {
    "time": 1,  # FullTimeString24
    "rank": 11,  # TradeRank
    "dollars": 8,  # Dollars
    "multiplier": 9,  # DollarsMultiplier
}
_SORT_DEFAULT_DIRECTION: dict[str, str] = {
    "time": "desc",  # newest first
    "rank": "asc",  # best rank first
    "dollars": "desc",  # biggest first
    "multiplier": "desc",  # most unusual first
}


def _resolve_dates(
    *,
    tickers: str,
    start_date: str,
    end_date: str,
) -> tuple[str, str]:
    """Pick date range defaults based on query scope.

    Single-ticker queries default to a 90-day lookback window.
    Broad scans (no tickers) default to today only.
    Explicit caller values always win.
    """
    eff_end = end_date if end_date else today_date_string()
    if start_date:
        eff_start = start_date
    elif tickers:
        eff_start = ninety_days_ago_date_string()
    else:
        eff_start = eff_end
    return eff_start, eff_end


def _resolve_include_flags(*, tickers: str) -> tuple[int, int]:
    """Pick phantom/offsetting defaults based on query scope.

    Single-ticker queries include phantom and offsetting trades by
    default for a complete picture. Broad scans exclude them to
    reduce noise.
    """
    if tickers:
        return _TICKER_INCLUDE_PHANTOM, _TICKER_INCLUDE_OFFSETTING
    return _BROAD_INCLUDE_PHANTOM, _BROAD_INCLUDE_OFFSETTING


def _format_time(trade: Trade) -> str:
    """Extract compact HH:MM time from the trade timestamp.

    Prefers the 24-hour time string when available, falling back
    to parsing the ISO datetime string.
    """
    if trade.full_time_string24:
        return trade.full_time_string24[:5]
    if trade.full_date_time:
        parts = trade.full_date_time.split("T", maxsplit=1)
        return parts[1][:5] if len(parts) == 2 else trade.full_date_time
    return ""


def _collect_trade_types(trade: Trade) -> list[str]:
    """Collect active trade type flags into a compact list.

    Returns ["block"] when no special trade type flags are set,
    explicitly indicating a standard institutional block trade.
    Combines the individual boolean flags into a single list for
    token-efficient MCP responses.
    """
    types: list[str] = []
    if trade.dark_pool:
        types.append("dark_pool")
    if trade.sweep:
        types.append("sweep")
    if trade.late_print:
        types.append("late_print")
    if trade.signature_print:
        types.append("signature_print")
    if trade.opening_trade:
        types.append("opening")
    if trade.closing_trade:
        types.append("closing")
    if trade.phantom_print:
        types.append("phantom")
    return types if types else ["block"]


def _curate_trade(
    trade: Trade,
    snapshots: dict[str, float],
) -> dict[str, Any]:
    """Return compact trade fields for MCP consumption.

    Field definitions:
      ticker: Symbol of the stock/ETF.
      date: Trade date in YYYY-MM-DD format.
      time: When the block trade occurred (HH:MM, 24-hour format).
        When trade_count > 1, this is the timestamp of the last
        print in the block.
      price: Price at which the block trade executed. When
        trade_count > 1, this is the price of the last print.
      current_price: Live price from snapshot data. None when
        snapshot lookup fails or ticker not in snapshot map.
      dollars: Formatted total dollar volume of the trade ("$315.8M",
        "$1.2B"). Summed across all prints when trade_count > 1.
      volume: Share volume of the trade (summed across all prints).
      trade_rank: Significance rank within the current query scope.
        For broad scans, rank is relative to all trades matching
        the filters on that day. For ticker queries, rank is
        relative to that ticker's trades in the date range.
        1 = most significant by dollar volume, 9999 = unranked.
      dollars_multiplier: This trade's dollar volume relative to
        typical institutional activity. Higher = more unusual.
      cumulative_distribution: Percentile of institutional dollar
        volume (0.0-1.0). Values near 1.0 mean this trade is among
        the largest seen. Note: with trade_rank=100 (default), most
        values will be 0.95+ since small trades are already filtered.
      trade_count: Number of individual prints composing this block.
        When > 1, the trade is an aggregation of multiple prints
        at the same price within a short window.
      types: Trade type classification. ["block"] for standard
        institutional block trades. Special types include dark_pool,
        sweep, late_print, signature_print, opening, closing,
        phantom. Multiple flags can be active simultaneously.
      sector: Market sector for stocks, category/description for
        ETFs (e.g. "Industrials", "Large Caps", "2x Bull DJIA").
      last_comparable_date: When a similar-sized trade last occurred
        for this ticker. None if no prior comparable trade exists.
    """
    return {
        "ticker": trade.ticker,
        "date": format_date(trade.date),
        "time": _format_time(trade),
        "price": trade.price,
        "current_price": snapshots.get(trade.ticker),
        "dollars": format_dollars(trade.dollars),
        "volume": trade.volume,
        "trade_rank": trade.trade_rank,
        "dollars_multiplier": round(trade.dollars_multiplier, 2),
        "cumulative_distribution": trade.cumulative_distribution,
        "trade_count": trade.trade_count,
        "types": _collect_trade_types(trade),
        "sector": trade.sector,
        "last_comparable_date": format_date(trade.last_comparible_trade_date),
    }


@mcp.tool
def trades(
    tickers: Annotated[
        str,
        Field(
            description=(
                "Comma-separated ticker symbols to filter "
                "(e.g. 'AAPL' or 'AAPL,MSFT'). "
                "Empty string scans all tickers."
            ),
        ),
    ] = "",
    start_date: Annotated[
        str,
        Field(
            description=(
                "Start of the date range in YYYY-MM-DD format. "
                "Defaults to today for broad scans, "
                "90 days ago for ticker-specific queries."
            ),
        ),
    ] = "",
    end_date: Annotated[
        str,
        Field(
            description=(
                "End of the date range in YYYY-MM-DD format. Defaults to today."
            ),
        ),
    ] = "",
    trade_rank: Annotated[
        int,
        Field(
            ge=-1,
            le=9999,
            description=(
                "Maximum trade rank filter. Only trades ranked at or "
                "above this threshold are returned. "
                "100 = ranked trades only. -1 = no filter. "
                "Defaults to 100 (ranked only)."
            ),
        ),
    ] = 100,
    min_dollars: Annotated[
        float,
        Field(
            ge=0,
            description="Minimum dollar value filter. Defaults to $500K.",
        ),
    ] = 500_000,
    min_volume: Annotated[
        int,
        Field(
            ge=0,
            description="Minimum share volume filter. Defaults to 10,000.",
        ),
    ] = 10_000,
    sort_by: Annotated[
        str,
        Field(
            description=(
                "Sort results by: time (newest first), rank (best "
                "first), dollars (biggest first), or multiplier "
                "(most unusual first). Defaults to time."
            ),
        ),
    ] = "time",
    offset: Annotated[
        int,
        Field(
            ge=0,
            description=(
                "Number of results to skip for pagination. "
                "Use with max_results to page through large result "
                "sets. Defaults to 0 (start from the beginning)."
            ),
        ),
    ] = 0,
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
    """Look up institutional block trades across all tickers or for specific symbols.

    An institutional **block trade** is a large-volume transaction
    typically executed by institutional investors (hedge funds, pension
    funds, mutual funds). These trades represent significant capital
    commitments and often signal institutional conviction at specific
    price levels.

    Context-aware defaults adjust automatically based on whether
    tickers are specified:
    - **Ticker queries**: 90-day lookback, include phantom and
      offsetting trades for a complete history
    - **Broad scans**: Today only, exclude phantom and offsetting
      trades to focus on actionable activity

    Key fields per trade:
    - trade_rank: significance ranking within the query scope
      (1 = most significant by dollar volume, 9999 = unranked).
      For broad scans, rank is among all trades that day. For
      ticker queries, rank is among that ticker's trades in the
      date range. Default filter is 100 (ranked only).
    - dollars_multiplier: how unusual this trade is relative to
      typical institutional activity (higher = more unusual)
    - types: trade classification. ["block"] for standard block
      trades; special types include dark_pool, sweep, late_print,
      signature_print, opening, closing, phantom
    - last_comparable_date: when a similar-sized trade last occurred
    - trade_count: when > 1, the trade aggregates multiple prints
      at the same price. dollars/volume are summed; price/time
      reflect the last print.

    Results are sorted by the sort_by parameter (default: time
    descending). Use offset + max_results for pagination.
    """
    eff_start, eff_end = _resolve_dates(
        tickers=tickers,
        start_date=start_date,
        end_date=end_date,
    )
    eff_phantom, eff_offsetting = _resolve_include_flags(tickers=tickers)
    sort_by = normalize_sort_by(sort_by)
    col_index = _SORT_COLUMN_INDEX.get(sort_by, _SORT_COLUMN_INDEX["time"])
    col_dir = _SORT_DEFAULT_DIRECTION.get(sort_by, "desc")
    warnings: list[str] = []
    client = resolve_client(ctx)

    trades_data: list[dict[str, Any]] | None = None
    total_count: int | None = None
    try:
        raw_trades = get_trades(
            client,
            tickers=tickers,
            start_date=eff_start,
            end_date=eff_end,
            trade_rank=trade_rank,
            min_dollars=min_dollars,
            min_volume=min_volume,
            include_phantom=eff_phantom,
            include_offsetting=eff_offsetting,
            start=offset,
            length=max_results,
            order_column_index=col_index,
            order_direction=col_dir,
        )
        snapshots = fetch_snapshot_prices(client, warnings=warnings)
        trades_data = [_curate_trade(t, snapshots) for t in raw_trades]
        total_count = raw_trades[0].total_rows if raw_trades else 0
    except Exception as error:
        capture_non_auth_error(warnings, "Failed to fetch trades", error)

    result: dict[str, Any] = {}
    result["data"] = {"trades": trades_data}
    if warnings:
        result["warnings"] = warnings
    result["metadata"] = {
        "trade_count": count_rows(trades_data),
        "total_available": total_count,
    }
    return result
