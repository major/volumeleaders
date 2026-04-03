"""Tests for parsing helpers in volumeleaders._parsing."""

from collections.abc import Callable
from datetime import datetime, timezone
from importlib import import_module

import pytest

_parsing = import_module("volumeleaders._parsing")
format_date = _parsing.format_date
format_datekey = _parsing.format_datekey
parse_aspnet_date = _parsing.parse_aspnet_date
parse_datekey = _parsing.parse_datekey
parse_snapshot_string = _parsing.parse_snapshot_string


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("/Date(-62135596800000)/", None),
        ("/Date(-2208988800000)/", None),
    ],
)
def test_parse_aspnet_date_handles_null_sentinels(raw: str, expected: None) -> None:
    """Ensure known ASP.NET null sentinel values map to None."""
    assert parse_aspnet_date(raw) is expected


@pytest.mark.parametrize("raw", [None, "", "not-a-date", "/Date(bad)/"])
def test_parse_aspnet_date_handles_empty_and_malformed_values(raw: str | None) -> None:
    """Return None for missing and malformed ASP.NET date values."""
    assert parse_aspnet_date(raw) is None


def test_parse_aspnet_date_parses_normal_date() -> None:
    """Parse a valid ASP.NET date string into a UTC datetime."""
    parsed = parse_aspnet_date("/Date(1775001600000)/")
    assert parsed == datetime(2026, 4, 1, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        pytest.param(
            "AAPL:255.30;SPY:655.24;MSFT:369.37",
            {"AAPL": 255.30, "SPY": 655.24, "MSFT": 369.37},
            id="multiple_pairs",
        ),
        pytest.param("", {}, id="empty_string"),
        pytest.param("SPY:655.24", {"SPY": 655.24}, id="single_pair"),
        pytest.param(
            "SPY:655.24;badpair;QQQ:not-a-float;AAPL:255.3",
            {"SPY": 655.24, "AAPL": 255.3},
            id="skips_malformed",
        ),
    ],
)
def test_parse_snapshot_string(raw: str, expected: dict[str, float]) -> None:
    """Parse snapshot strings into ticker-price mappings, handling edge cases."""
    assert parse_snapshot_string(raw) == expected


@pytest.mark.parametrize(
    ("datekey", "expected"),
    [
        (20260401, datetime(2026, 4, 1, tzinfo=timezone.utc)),
        (20000101, datetime(2000, 1, 1, tzinfo=timezone.utc)),
    ],
)
def test_parse_datekey_parses_valid_values(datekey: int, expected: datetime) -> None:
    """Convert integer date keys into timezone-aware UTC datetimes."""
    assert parse_datekey(datekey) == expected


@pytest.mark.parametrize("datekey", [20260229, 20261301, 20260001])
def test_parse_datekey_raises_for_invalid_values(datekey: int) -> None:
    """Raise ValueError when the datekey does not represent a real date."""
    with pytest.raises(ValueError):
        parse_datekey(datekey)


@pytest.mark.parametrize(
    ("formatter", "expected"),
    [
        pytest.param(format_datekey, "20260401", id="datekey_YYYYMMDD"),
        pytest.param(format_date, "2026-04-01", id="date_ISO"),
    ],
)
def test_date_formatting(formatter: Callable[[datetime], str], expected: str) -> None:
    """Format datetime values into API-compatible date strings."""
    assert formatter(datetime(2026, 4, 1, tzinfo=timezone.utc)) == expected
