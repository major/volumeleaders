"""Parsers for VolumeLeaders response formats.

Handles ASP.NET date serialization, snapshot string parsing, and
other response normalization.
"""

from __future__ import annotations

import re
from datetime import datetime, timezone

# ASP.NET serializes dates as /Date(epoch_ms)/ with optional timezone offset.
_ASPNET_DATE_RE = re.compile(r"/Date\((-?\d+)\)/")

# Sentinel epoch values that mean "no date" in the VL API.
# -62135596800000 ms = 0001-01-01 (C# DateTime.MinValue)
# -2208988800000 ms = 1900-01-01 (another null sentinel)
_NULL_EPOCH_MS: frozenset[int] = frozenset({-62135596800000, -2208988800000})

# Trade rank value meaning "unranked" (beyond top 100).
UNRANKED_SENTINEL = 9999


def parse_aspnet_date(value: str | None) -> datetime | None:
    """Parse an ASP.NET /Date(epoch_ms)/ string to a timezone-aware datetime.

    Returns None for null sentinels (DateTime.MinValue, 1900-01-01) or
    if the value is None/empty.
    """
    if not value:
        return None

    match = _ASPNET_DATE_RE.search(value)
    if not match:
        return None

    epoch_ms = int(match.group(1))
    if epoch_ms in _NULL_EPOCH_MS:
        return None

    return datetime.fromtimestamp(epoch_ms / 1000, tz=timezone.utc)


def parse_snapshot_string(raw: str) -> dict[str, float]:
    """Parse the GetAllSnapshots response into a ticker-price mapping.

    The API returns a semicolon-delimited string like:
        "A:114.73;AA:70.96;AAPL:255.30;..."

    Returns a dict mapping ticker symbols to their current prices.
    """
    result: dict[str, float] = {}
    if not raw:
        return result

    for pair in raw.split(";"):
        if ":" not in pair:
            continue
        ticker, price_str = pair.split(":", maxsplit=1)
        try:
            result[ticker] = float(price_str)
        except ValueError:
            # Skip malformed entries rather than crashing.
            continue

    return result


def parse_datekey(datekey: int) -> datetime:
    """Parse a YYYYMMDD integer date key to a timezone-aware datetime.

    Example: 20260401 -> 2026-04-01T00:00:00+00:00
    """
    year = datekey // 10000
    month = (datekey % 10000) // 100
    day = datekey % 100
    return datetime(year, month, day, tzinfo=timezone.utc)


def format_datekey(dt: datetime) -> str:
    """Format a datetime as a YYYYMMDD string for API requests.

    Example: datetime(2026, 4, 1) -> "20260401"
    """
    return dt.strftime("%Y%m%d")


def format_date(dt: datetime) -> str:
    """Format a datetime as YYYY-MM-DD for API requests.

    Example: datetime(2026, 4, 1) -> "2026-04-01"
    """
    return dt.strftime("%Y-%m-%d")
