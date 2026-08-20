"""MCP tool for dark pool volume profile and Point-of-Control analysis."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated, Any

from fastmcp.dependencies import CurrentContext
from pydantic import Field

from volumeleaders._exceptions import APIError
from volumeleaders.endpoints.darkpool import get_dark_pool_volume_report
from volumeleaders.mcp import mcp
from volumeleaders.mcp.utils import (
    capture_non_auth_error,
    count_rows,
    format_dollars,
    one_week_ago_date_string,
    resolve_client,
    today_date_string,
)

_DEFAULT_CONTEXT = CurrentContext()

if TYPE_CHECKING:
    from fastmcp import Context

    from volumeleaders._client import VolumeLeadersClient
    from volumeleaders.models import DarkPoolVolumeBin


def _classify_poc_relation(last_close: float, low: float, high: float) -> str:
    """Classify POC position relative to the latest close price."""
    if last_close < low:
        return "Above Close (Resistance Overhead)"
    if last_close > high:
        return "Below Close (Underlying Support)"
    return "At Close"


def _aggregate_ticker_bins(
    rows: list[DarkPoolVolumeBin],
) -> tuple[dict[int, dict[str, Any]], float, float, float]:
    """Aggregate multi-week dark pool volume per price bin for a single ticker."""
    bins: dict[int, dict[str, Any]] = {}
    last_close = rows[0].last_close if rows else 0.0
    range_min = rows[0].range_min_price if rows else 0.0
    range_max = rows[0].range_max_price if rows else 0.0

    for r in rows:
        bid = r.bin_id
        if bid not in bins:
            bins[bid] = {
                "bin_id": bid,
                "bin_low": r.bin_low,
                "bin_high": r.bin_high,
                "dp_dollars": 0.0,
            }
        bins[bid]["dp_dollars"] += r.dp_dollars

    return bins, last_close, range_min, range_max


def _curate_ticker_profile(
    ticker: str,
    rows: list[DarkPoolVolumeBin],
    *,
    top_nodes_only: bool,
) -> dict[str, Any]:
    """Curate a compact volume-by-price profile for a single ticker."""
    bins_map, last_close, range_min, range_max = _aggregate_ticker_bins(rows)
    sorted_bins = sorted(
        bins_map.values(),
        key=lambda b: b["dp_dollars"],
        reverse=True,
    )

    total_dp = sum(b["dp_dollars"] for b in sorted_bins)
    poc = (
        sorted_bins[0]
        if sorted_bins
        else {"bin_low": 0.0, "bin_high": 0.0, "dp_dollars": 0.0}
    )

    poc_low = float(poc["bin_low"])
    poc_high = float(poc["bin_high"])
    poc_dollars = float(poc["dp_dollars"])
    poc_relation = _classify_poc_relation(last_close, poc_low, poc_high)

    base: dict[str, Any] = {
        "ticker": ticker,
        "last_close": last_close,
        "total_dp_dollars": format_dollars(total_dp),
        "price_range": f"${range_min:.2f} - ${range_max:.2f}",
        "poc_price_range": f"${poc_low:.2f} - ${poc_high:.2f}",
        "poc_dp_dollars": format_dollars(poc_dollars),
        "poc_relation": poc_relation,
    }

    if top_nodes_only:
        top_nodes = [b for b in sorted_bins if b["dp_dollars"] > 0][:3]
        base["top_accumulation_nodes"] = [
            {
                "price_range": f"${b['bin_low']:.2f} - ${b['bin_high']:.2f}",
                "dp_dollars": format_dollars(b["dp_dollars"]),
                "share_of_total_pct": (
                    round(b["dp_dollars"] / total_dp * 100, 1) if total_dp > 0 else 0.0
                ),
            }
            for b in top_nodes
        ]
    else:
        all_ordered = sorted(bins_map.values(), key=lambda b: b["bin_id"])
        base["bins"] = [
            {
                "bin_id": b["bin_id"],
                "price_range": f"${b['bin_low']:.2f} - ${b['bin_high']:.2f}",
                "dp_dollars": format_dollars(b["dp_dollars"]),
            }
            for b in all_ordered
        ]

    return base


def _fetch_dark_pool_report(  # noqa: PLR0913
    client: VolumeLeadersClient,
    start_date: str,
    end_date: str,
    bins: int,
    clean_tickers: str,
    warnings: list[str],
) -> list[DarkPoolVolumeBin]:
    """Fetch raw dark pool volume report with error capture."""
    try:
        return get_dark_pool_volume_report(
            client,
            last_trade_date=end_date,
            start_date=start_date,
            end_date=end_date,
            bins=bins,
            tickers=clean_tickers,
        )
    except APIError as error:
        capture_non_auth_error(warnings, "Failed to fetch dark pool report", error)
        return []


def _group_by_requested_tickers(
    rows: list[DarkPoolVolumeBin],
    clean_tickers: str,
) -> dict[str, list[DarkPoolVolumeBin]]:
    """Group rows by ticker filtering to requested symbols."""
    ticker_filter = {t.strip().upper() for t in clean_tickers.split(",") if t.strip()}
    by_ticker: dict[str, list[DarkPoolVolumeBin]] = {}
    for r in rows:
        t_up = r.ticker.upper()
        if not ticker_filter or t_up in ticker_filter:
            by_ticker.setdefault(t_up, []).append(r)
    return by_ticker


@mcp.tool
def dark_pool_profile(  # noqa: PLR0913
    tickers: Annotated[
        str,
        Field(
            description=(
                "Comma-separated ticker symbols to profile (e.g. 'SPY,QQQ,AAPL'). "
                "Required."
            ),
        ),
    ],
    start_date: Annotated[
        str,
        Field(
            description="Start date in YYYY-MM-DD format. Defaults to one week ago.",
        ),
    ] = "",
    end_date: Annotated[
        str,
        Field(
            description="End date in YYYY-MM-DD format. Defaults to today.",
        ),
    ] = "",
    top_nodes_only: Annotated[  # noqa: FBT002
        bool,
        Field(
            description=(
                "Return top 3 volume accumulation nodes and Point-of-Control (POC) "
                "instead of all price bins. Defaults to True."
            ),
        ),
    ] = True,
    bins: Annotated[
        int,
        Field(
            description="Number of price bins to compute (default 24).",
        ),
    ] = 24,
    include_query: Annotated[  # noqa: FBT002
        bool,
        Field(
            description="Include resolved query parameters in response.",
        ),
    ] = False,
    ctx: Context = _DEFAULT_CONTEXT,
) -> dict[str, Any]:
    """Analyze dark pool volume-by-price distribution and Point-of-Control."""
    client = resolve_client(ctx)
    resolved_start = start_date or one_week_ago_date_string()
    resolved_end = end_date or today_date_string()
    warnings: list[str] = []

    clean_tickers = ",".join(t.strip().upper() for t in tickers.split(",") if t.strip())

    if not clean_tickers:
        return {
            "data": [],
            "metadata": {
                "tickers_count": 0,
                "start_date": resolved_start,
                "end_date": resolved_end,
            },
            "warnings": ["No ticker symbols provided"],
        }

    raw_rows = _fetch_dark_pool_report(
        client,
        resolved_start,
        resolved_end,
        bins,
        clean_tickers,
        warnings,
    )
    by_ticker = _group_by_requested_tickers(raw_rows, clean_tickers)

    curated = [
        _curate_ticker_profile(t_symbol, t_rows, top_nodes_only=top_nodes_only)
        for t_symbol, t_rows in by_ticker.items()
    ]

    envelope: dict[str, Any] = {
        "data": curated,
        "metadata": {
            "tickers_count": count_rows(curated),
            "start_date": resolved_start,
            "end_date": resolved_end,
            "top_nodes_only": top_nodes_only,
        },
    }

    if include_query:
        envelope["query"] = {
            "tickers": clean_tickers,
            "start_date": resolved_start,
            "end_date": resolved_end,
            "top_nodes_only": top_nodes_only,
            "bins": bins,
        }

    if warnings:
        envelope["warnings"] = warnings

    return envelope
