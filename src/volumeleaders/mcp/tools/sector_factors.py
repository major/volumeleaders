"""MCP tool for multi-factor sector performance and risk scorecard."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Annotated, Any

from fastmcp.dependencies import CurrentContext
from pydantic import Field

from volumeleaders._exceptions import APIError
from volumeleaders.endpoints.sector import get_sector_daily_returns
from volumeleaders.mcp import mcp
from volumeleaders.mcp.utils import (
    capture_non_auth_error,
    format_datekey_to_iso,
    ninety_days_ago_date_string,
    resolve_client,
    today_date_string,
)

_DEFAULT_CONTEXT = CurrentContext()

if TYPE_CHECKING:
    from fastmcp import Context

    from volumeleaders._client import VolumeLeadersClient
    from volumeleaders.models import SectorDailyReturn


def _parse_filter_set(filter_str: str) -> set[str]:
    """Parse a comma-separated filter string into a case-folded set."""
    if not filter_str.strip():
        return set()
    return {s.strip().casefold() for s in filter_str.split(",") if s.strip()}


def _extract_timeframe_metrics(
    row: SectorDailyReturn,
    timeframe: str,
) -> tuple[float, float, float, float, float]:
    """Extract beta, momentum, realized_vol, relative_strength, and sharpe."""
    tf = timeframe.lower().strip()
    if tf in {"10", "10d", "10-day"}:
        return (
            row.beta_10,
            row.momentum_10,
            row.realized_vol_10,
            row.relative_strength_10,
            row.sharpe_10,
        )
    if tf in {"20", "20d", "20-day"}:
        return (
            row.beta_20,
            row.momentum_20,
            row.realized_vol_20,
            row.relative_strength_20,
            row.sharpe_20,
        )
    if tf in {"40", "40d", "40-day"}:
        return (
            row.beta_40,
            row.momentum_40,
            row.realized_vol_40,
            row.relative_strength_40,
            row.sharpe_40,
        )
    return (
        row.beta_blended,
        row.momentum_blended,
        row.realized_vol_blended,
        row.relative_strength_blended,
        row.sharpe_blended,
    )


def _curate_sector_factor_row(
    row: SectorDailyReturn,
    timeframe: str,
    metric: str,
) -> dict[str, Any]:
    """Curate a single sector factor row with formatted metrics."""
    beta, mom, vol, rs, sharpe = _extract_timeframe_metrics(row, timeframe)
    base: dict[str, Any] = {
        "sector": row.sector,
        "date": format_datekey_to_iso(row.date_key),
    }

    m = metric.lower().strip()
    metric_map: dict[str, tuple[str, float]] = {
        "daily_return": ("daily_return_pct", round(row.sector_daily_return_pct, 2)),
        "daily_returns": ("daily_return_pct", round(row.sector_daily_return_pct, 2)),
        "advancers": ("pct_advancers", round(row.pct_tickers_positive, 1)),
        "advancer": ("pct_advancers", round(row.pct_tickers_positive, 1)),
        "pct_advancers": ("pct_advancers", round(row.pct_tickers_positive, 1)),
        "momentum": ("momentum_pct", round(mom * 100, 2)),
        "relative_strength": ("relative_strength_pct", round(rs * 100, 2)),
        "sharpe": ("sharpe", round(sharpe, 2)),
        "beta": ("beta", round(beta, 2)),
        "realized_vol": ("realized_vol_pct", round(vol * 100, 2)),
        "volatility": ("realized_vol_pct", round(vol * 100, 2)),
        "vol": ("realized_vol_pct", round(vol * 100, 2)),
    }

    if m in metric_map:
        key, val = metric_map[m]
        base[key] = val
        return base

    base.update(
        {
            "daily_return_pct": round(row.sector_daily_return_pct, 2),
            "pct_advancers": round(row.pct_tickers_positive, 1),
            "momentum_pct": round(mom * 100, 2),
            "relative_strength_pct": round(rs * 100, 2),
            "sharpe": round(sharpe, 2),
            "beta": round(beta, 2),
            "realized_vol_pct": round(vol * 100, 2),
        },
    )
    return base


def _resolve_factor_dates(date: str) -> tuple[str, str]:
    """Resolve start and end date strings for 90-day factor lookback."""
    end = date or today_date_string()
    try:
        dt = datetime.fromisoformat(end.strip())
        start = (dt - timedelta(days=90)).strftime("%Y-%m-%d")
    except ValueError:
        start = ninety_days_ago_date_string()
    return start, end


def _fetch_sector_returns(
    client: VolumeLeadersClient,
    start_date: str,
    end_date: str,
    warnings: list[str],
) -> list[SectorDailyReturn]:
    """Fetch raw sector returns with error capture."""
    try:
        return get_sector_daily_returns(
            client,
            start_date=start_date,
            end_date=end_date,
        )
    except APIError as error:
        capture_non_auth_error(warnings, "Failed to fetch sector factors", error)
        return []


def _select_target_slice(
    rows: list[SectorDailyReturn],
    fallback_date: str,
) -> tuple[list[SectorDailyReturn], float | None, str]:
    """Select target rows for the latest date key and extract benchmark metadata."""
    if not rows:
        return [], None, fallback_date
    latest_dk = max(r.date_key for r in rows)
    target = [r for r in rows if r.date_key == latest_dk]
    spy_close = target[0].spy_close if target else None
    return target, spy_close, format_datekey_to_iso(latest_dk)


@mcp.tool
def sector_factors(  # noqa: PLR0913
    date: Annotated[
        str,
        Field(
            description=(
                "Query date in YYYY-MM-DD format. Defaults to the latest available "
                "trading date in the system."
            ),
        ),
    ] = "",
    timeframe: Annotated[
        str,
        Field(
            description="Lookback timeframe: 'blended' (default), '10d', '20d', '40d'.",
        ),
    ] = "blended",
    metric: Annotated[
        str,
        Field(
            description=(
                "Factor metric: 'all' (default), 'momentum', 'relative_strength', "
                "'sharpe', 'beta', 'realized_vol', 'daily_returns', 'advancers'."
            ),
        ),
    ] = "all",
    sectors: Annotated[
        str,
        Field(
            description=(
                "Comma-separated sector names to filter (e.g. 'Technology,Energy'). "
                "Empty string returns all sectors."
            ),
        ),
    ] = "",
    include_query: Annotated[  # noqa: FBT002
        bool,
        Field(
            description="Include resolved query parameters in response.",
        ),
    ] = False,
    ctx: Context = _DEFAULT_CONTEXT,
) -> dict[str, Any]:
    """Score market sectors across multi-factor momentum and risk."""
    client = resolve_client(ctx)
    resolved_start, resolved_end = _resolve_factor_dates(date)
    warnings: list[str] = []

    raw_rows = _fetch_sector_returns(client, resolved_start, resolved_end, warnings)
    target_rows, spy_close, as_of_date = _select_target_slice(raw_rows, resolved_end)

    sector_set = _parse_filter_set(sectors)
    curated = [
        _curate_sector_factor_row(r, timeframe=timeframe, metric=metric)
        for r in target_rows
        if not sector_set or r.sector.casefold() in sector_set
    ]

    envelope: dict[str, Any] = {
        "data": curated,
        "metadata": {
            "sectors_count": len(curated),
            "date": as_of_date,
            "timeframe": timeframe,
            "metric": metric,
            "benchmark": "SPY",
            "spy_close": spy_close,
        },
    }

    if include_query:
        envelope["query"] = {
            "date": date,
            "timeframe": timeframe,
            "metric": metric,
            "sectors": sectors,
        }

    if warnings:
        envelope["warnings"] = warnings

    return envelope
