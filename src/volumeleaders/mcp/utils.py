"""Shared utilities for MCP tool implementations."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from fastmcp import Context

from volumeleaders._client import VolumeLeadersClient
from volumeleaders._exceptions import (
    APIError,
    AuthenticationError,
    CookieExtractionError,
)
from volumeleaders.endpoints.exhaustion import get_exhaustion_scores
from volumeleaders.endpoints.trades import get_all_snapshots
from volumeleaders.mcp import VLContext
from volumeleaders.models import ExhaustionScore


def resolve_client(ctx: Context) -> VolumeLeadersClient:
    """Return the shared VolumeLeaders client from lifespan context."""
    lifespan_context = getattr(ctx, "lifespan_context", None)
    if isinstance(lifespan_context, VLContext):
        return lifespan_context.client
    raise RuntimeError("MCP lifespan context is missing VolumeLeaders client")


def is_auth_failure(error: Exception) -> bool:
    """Return True when an error strongly indicates an auth failure."""
    if isinstance(error, (AuthenticationError, CookieExtractionError)):
        return True
    if isinstance(error, APIError) and error.status_code in {401, 403}:
        return True
    return "login" in str(error).lower()


def capture_non_auth_error(warnings: list[str], message: str, error: Exception) -> None:
    """Record non-auth errors as warnings while letting auth failures propagate."""
    if is_auth_failure(error):
        raise error
    warnings.append(f"{message}: {error}")


def today_date_string() -> str:
    """Return the current UTC date in YYYY-MM-DD format."""
    return datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")


def one_week_ago_date_string() -> str:
    """Return the UTC date one week ago in YYYY-MM-DD format."""
    return (datetime.now(tz=timezone.utc) - timedelta(weeks=1)).strftime("%Y-%m-%d")


def ninety_days_ago_date_string() -> str:
    """Return the UTC date 90 days ago in YYYY-MM-DD format."""
    return (datetime.now(tz=timezone.utc) - timedelta(days=90)).strftime("%Y-%m-%d")


def one_year_ago_date_string() -> str:
    """Return the UTC date one year ago in YYYY-MM-DD format."""
    return (datetime.now(tz=timezone.utc) - timedelta(days=365)).strftime("%Y-%m-%d")


def count_rows(rows: list[Any] | None) -> int | None:
    """Return list length when present, otherwise None."""
    if rows is None:
        return None
    return len(rows)


def curate_exhaustion(exhaustion: ExhaustionScore) -> dict[str, int]:
    """Return compact exhaustion data for MCP responses."""
    return {
        "date_key": exhaustion.date_key,
        "exhaustion_score_rank": exhaustion.exhaustion_score_rank,
        "exhaustion_score_rank_30_day": exhaustion.exhaustion_score_rank_30_day,
        "exhaustion_score_rank_90_day": exhaustion.exhaustion_score_rank_90_day,
        "exhaustion_score_rank_365_day": exhaustion.exhaustion_score_rank_365_day,
    }


def format_date(dt: datetime | None) -> str | None:
    """Format an optional datetime as a YYYY-MM-DD string.

    Returns None when the input is None (e.g. ASP.NET sentinel dates
    that parsed to null).
    """
    if dt is None:
        return None
    return dt.strftime("%Y-%m-%d")


def format_dollars(amount: float) -> str:
    """Format a dollar amount into a compact human-readable string.

    Examples: 1_500_000_000 -> "$1.5B", 42_000_000 -> "$42.0M",
    8_500 -> "$8K", 750 -> "$750".
    """
    if amount >= 1_000_000_000:
        return f"${amount / 1_000_000_000:.1f}B"
    if amount >= 1_000_000:
        return f"${amount / 1_000_000:.1f}M"
    if amount >= 1_000:
        return f"${amount / 1_000:.0f}K"
    return f"${amount:.0f}"


def fetch_snapshot_prices(
    client: VolumeLeadersClient,
    *,
    warnings: list[str],
) -> dict[str, float]:
    """Fetch the ticker-to-price snapshot map with warning fallback.

    Returns the full snapshot dict on success, or an empty dict if
    the fetch fails (non-auth errors are captured as warnings).
    Efficient for enriching multi-ticker results with current prices
    via a single API call.
    """
    try:
        return get_all_snapshots(client)
    except Exception as error:
        capture_non_auth_error(warnings, "Failed to fetch snapshot prices", error)
        return {}


# Maps informal sort names to canonical sort keys used by tool _SORT_COLUMN_INDEX
# dicts. Canonical keys (time, rank, dollars, multiplier) pass through unchanged.
_SORT_ALIASES: dict[str, str] = {
    # multiplier aliases
    "rs": "multiplier",
    "relative_size": "multiplier",
    "relative size": "multiplier",
    "unusual": "multiplier",
    # dollars aliases
    "biggest": "dollars",
    "largest": "dollars",
    "size": "dollars",
    # rank aliases
    "best": "rank",
    "top": "rank",
    # time aliases
    "newest": "time",
    "latest": "time",
    "recent": "time",
}


def normalize_sort_by(value: str) -> str:
    """Translate sort aliases to canonical sort keys.

    Accepts informal names like "RS", "relative_size", or "biggest"
    and maps them to the canonical keys (time, rank, dollars, multiplier)
    that tool sort dicts understand. Unrecognized values pass through
    unchanged so the caller's fallback logic handles them.
    """
    return _SORT_ALIASES.get(value.lower().strip(), value)


def fetch_exhaustion_data(
    client: VolumeLeadersClient,
    *,
    query_date: str,
    warnings: list[str],
) -> dict[str, int] | None:
    """Fetch curated exhaustion score data with warning fallback."""
    try:
        return curate_exhaustion(get_exhaustion_scores(client, date=query_date))
    except Exception as error:
        capture_non_auth_error(warnings, "Failed to fetch exhaustion scores", error)
        return None
