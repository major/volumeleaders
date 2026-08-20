"""MCP tool for JdK Relative Rotation Graph (RRG) sector rotation modeling."""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Annotated, Any

from fastmcp.dependencies import CurrentContext
from pydantic import Field

from volumeleaders._exceptions import APIError
from volumeleaders.endpoints.sector import get_sector_daily_returns
from volumeleaders.mcp import mcp
from volumeleaders.mcp.utils import (
    capture_non_auth_error,
    format_datekey_to_iso,
    one_year_ago_date_string,
    resolve_client,
    today_date_string,
)

_DEFAULT_CONTEXT = CurrentContext()

_EQUITY_SECTORS: frozenset[str] = frozenset({
    "Technology",
    "Healthcare",
    "Financial Services",
    "Consumer Discretionary",
    "Consumer Staples",
    "Industrials",
    "Energy",
    "Materials",
    "Real Estate",
    "Utilities",
    "Communication Services",
})

if TYPE_CHECKING:
    from fastmcp import Context

    from volumeleaders._client import VolumeLeadersClient
    from volumeleaders.models import SectorDailyReturn


def _sma(values: list[float | None], end_idx: int, period: int) -> float | None:
    """Compute Simple Moving Average of a slice ending at end_idx."""
    if end_idx + 1 < period:
        return None
    sub = values[end_idx - period + 1 : end_idx + 1]
    if any(x is None for x in sub):
        return None
    return sum(float(x) for x in sub if x is not None) / period


def _std_sample(
    values: list[float | None],
    end_idx: int,
    period: int,
) -> float | None:
    """Compute sample standard deviation of a slice ending at end_idx."""
    mean = _sma(values, end_idx, period)
    if mean is None or period < 2:
        return None
    sub = values[end_idx - period + 1 : end_idx + 1]
    if any(x is None for x in sub):
        return None
    var = sum((float(x) - mean) ** 2 for x in sub if x is not None) / (
        period - 1
    )
    return math.sqrt(var) if var > 0 else None


def _normalize_100(
    values: list[float | None],
    end_idx: int,
    lookback: int,
) -> float | None:
    """Normalize a series value to a 100-centered Z-score band."""
    current = values[end_idx]
    if current is None:
        return None
    mean = _sma(values, end_idx, lookback)
    std = _std_sample(values, end_idx, lookback)
    if mean is None or std is None or std < 1e-12:
        return None
    return 100.0 + 10.0 * ((float(current) - mean) / std)


def _build_relative_points(
    rows: list[SectorDailyReturn],
) -> list[dict[str, Any]]:
    """Build cumulative price relative series against SPY benchmark."""
    sorted_rows = sorted(rows, key=lambda r: r.date_key)
    rel = 100.0
    prev_spy: float | None = None
    points: list[dict[str, Any]] = []

    for r in sorted_rows:
        spy = r.spy_close
        ret = (
            r.sector_daily_return_pct / 100.0
            if r.sector_daily_return_pct is not None
            else r.sector_daily_return
        )
        if abs(ret) > 0.5:
            ret = ret / 100.0

        if spy <= 0:
            continue

        if prev_spy is not None:
            spy_ret = (spy / prev_spy) - 1.0
            denom = 1.0 + spy_ret
            if abs(denom) > 1e-12:
                rel = rel * ((1.0 + ret) / denom)

        points.append({"date_key": r.date_key, "rel": rel})
        prev_spy = spy

    return points


def _compute_rs_series(
    rel_values: list[float],
    window: int,
    roc_period: int,
) -> tuple[list[float | None], list[float | None]]:
    """Compute smoothed RS-Ratio and RS-Momentum series."""
    smoothed: list[float | None] = [
        _sma(rel_values, i, window)  # type: ignore[arg-type]
        for i in range(len(rel_values))
    ]

    rs_ratio: list[float | None] = [
        _normalize_100(smoothed, i, window) for i in range(len(smoothed))
    ]

    roc: list[float | None] = []
    for j in range(len(rs_ratio)):
        prev_j = rs_ratio[j - roc_period] if j >= roc_period else None
        curr_j = rs_ratio[j]
        if j < roc_period or curr_j is None or prev_j is None:
            roc.append(None)
        else:
            roc.append(curr_j - prev_j)

    rs_mom: list[float | None] = [
        _normalize_100(roc, k, window) for k in range(len(roc))
    ]
    return rs_ratio, rs_mom


def _classify_quadrant(rs_ratio: float, rs_momentum: float) -> str:
    """Classify RRG quadrant based on RS-Ratio and RS-Momentum."""
    if rs_ratio >= 100.0:
        return "Leading" if rs_momentum >= 100.0 else "Weakening"
    return "Improving" if rs_momentum >= 100.0 else "Lagging"


def _determine_trajectory(trail: list[dict[str, Any]]) -> str:
    """Determine directional heading and momentum velocity from trail points."""
    if len(trail) < 2:
        return "Stable"
    dx = trail[-1]["rs_ratio"] - trail[-2]["rs_ratio"]
    dy = trail[-1]["rs_momentum"] - trail[-2]["rs_momentum"]
    if dx > 0 and dy > 0:
        return "North-East (Strengthening)"
    if dx > 0 and dy <= 0:
        return "South-East (Weakening Momentum)"
    if dx <= 0 and dy <= 0:
        return "South-West (Deteriorating)"
    return "North-West (Improving Momentum)"


def _compute_sector_rrg_model(
    rows: list[SectorDailyReturn],
    window: int,
    roc_period: int,
    trail_len: int,
) -> dict[str, Any] | None:
    """Compute RRG trail and current quadrant state for a single sector."""
    min_required = (2 * window) + roc_period + 2
    if len(rows) < min_required:
        return None

    points = _build_relative_points(rows)
    if len(points) < min_required:
        return None

    rel_values = [float(p["rel"]) for p in points]
    rs_ratio, rs_mom = _compute_rs_series(rel_values, window, roc_period)

    trail: list[dict[str, Any]] = []
    for t in range(len(points)):
        r_val = rs_ratio[t]
        m_val = rs_mom[t]
        if r_val is not None and m_val is not None:
            trail.append({
                "date": format_datekey_to_iso(points[t]["date_key"]),
                "rs_ratio": round(r_val, 1),
                "rs_momentum": round(m_val, 1),
            })

    if not trail:
        return None

    capped_trail = trail[-trail_len:]
    latest = capped_trail[-1]
    return {
        "sector": rows[0].sector,
        "quadrant": _classify_quadrant(
            latest["rs_ratio"],
            latest["rs_momentum"],
        ),
        "rs_ratio": latest["rs_ratio"],
        "rs_momentum": latest["rs_momentum"],
        "trajectory": _determine_trajectory(capped_trail),
        "trail": capped_trail,
    }


def _fetch_rrg_returns(
    client: VolumeLeadersClient,
    start_date: str,
    end_date: str,
    warnings: list[str],
) -> list[SectorDailyReturn]:
    """Fetch daily returns for RRG calculation with error capture."""
    try:
        return get_sector_daily_returns(
            client,
            start_date=start_date,
            end_date=end_date,
        )
    except APIError as error:
        capture_non_auth_error(warnings, "Failed to fetch sector daily returns", error)
        return []


def _group_by_eligible_sector(
    rows: list[SectorDailyReturn],
    equity_only: bool,
) -> dict[str, list[SectorDailyReturn]]:
    """Group rows by sector applying equity sector filter."""
    by_sector: dict[str, list[SectorDailyReturn]] = {}
    for r in rows:
        if equity_only and r.sector not in _EQUITY_SECTORS:
            continue
        by_sector.setdefault(r.sector, []).append(r)
    return by_sector


@mcp.tool
def sector_rotation_rrg(  # noqa: PLR0913
    window: Annotated[
        int,
        Field(
            description="Smoothing lookback window in trading days. Defaults to 20.",
        ),
    ] = 20,
    roc_period: Annotated[
        int,
        Field(
            description="Rate of change period for RS-Momentum. Defaults to 5.",
        ),
    ] = 5,
    trail_length: Annotated[
        int,
        Field(
            description="Number of historical trail bars to include (1-10). Defaults to 3.",
        ),
    ] = 3,
    equity_only: Annotated[
        bool,
        Field(
            description="Filter to equity market sectors only (excluding bonds and commodities). Defaults to True.",
        ),
    ] = True,
    sectors: Annotated[
        str,
        Field(
            description="Comma-separated sector names to filter. Empty string returns all candidate sectors.",
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
    """Analyze sector rotation using JdK Relative Rotation Graph (RRG) quadrant modeling vs SPY."""
    client = resolve_client(ctx)
    resolved_start = one_year_ago_date_string()
    resolved_end = today_date_string()
    warnings: list[str] = []

    raw_rows = _fetch_rrg_returns(client, resolved_start, resolved_end, warnings)
    by_sector = _group_by_eligible_sector(raw_rows, equity_only)

    target_sectors = {
        s.strip().casefold()
        for s in sectors.split(",")
        if s.strip()
    }

    curated: list[dict[str, Any]] = []
    w_clean = max(3, window)
    roc_clean = max(1, roc_period)
    t_clean = max(1, min(10, trail_length))

    for sector_name, sector_rows in sorted(by_sector.items()):
        if target_sectors and sector_name.casefold() not in target_sectors:
            continue
        res = _compute_sector_rrg_model(
            sector_rows,
            window=w_clean,
            roc_period=roc_clean,
            trail_len=t_clean,
        )
        if res is not None:
            curated.append(res)

    envelope: dict[str, Any] = {
        "data": curated,
        "metadata": {
            "sectors_count": len(curated),
            "benchmark": "SPY",
            "window": window,
            "roc_period": roc_period,
            "trail_length": trail_length,
            "equity_only": equity_only,
        },
    }

    if include_query:
        envelope["query"] = {
            "window": window,
            "roc_period": roc_period,
            "trail_length": trail_length,
            "equity_only": equity_only,
            "sectors": sectors,
        }

    if warnings:
        envelope["warnings"] = warnings

    return envelope
