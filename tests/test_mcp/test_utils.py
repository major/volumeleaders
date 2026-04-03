"""Tests for shared MCP utility functions."""

from __future__ import annotations

from importlib import import_module

import pytest

_utils = import_module("volumeleaders.mcp.utils")

format_dollars = _utils.format_dollars
normalize_sort_by = _utils.normalize_sort_by


@pytest.mark.parametrize(
    ("amount", "expected"),
    [
        (1_500_000_000, "$1.5B"),
        (1_000_000_000, "$1.0B"),
        (42_000_000, "$42.0M"),
        (1_000_000, "$1.0M"),
        (8_500, "$8K"),
        (1_000, "$1K"),
        (750, "$750"),
        (0, "$0"),
        (999_999_999, "$1000.0M"),
        (500_000, "$500K"),
        (12_345_678, "$12.3M"),
        (2_345_678_901, "$2.3B"),
    ],
)
def test_format_dollars(amount: float, expected: str) -> None:
    """Format dollar amounts into compact human-readable strings."""
    assert format_dollars(amount) == expected


@pytest.mark.parametrize(
    ("alias", "expected"),
    [
        # Canonical keys pass through unchanged.
        ("time", "time"),
        ("rank", "rank"),
        ("dollars", "dollars"),
        ("multiplier", "multiplier"),
        # Multiplier aliases.
        ("rs", "multiplier"),
        ("RS", "multiplier"),
        ("relative_size", "multiplier"),
        ("relative size", "multiplier"),
        ("unusual", "multiplier"),
        # Dollars aliases.
        ("biggest", "dollars"),
        ("largest", "dollars"),
        ("size", "dollars"),
        # Rank aliases.
        ("best", "rank"),
        ("top", "rank"),
        # Time aliases.
        ("newest", "time"),
        ("latest", "time"),
        ("recent", "time"),
        # Case and whitespace normalization.
        ("  RS  ", "multiplier"),
        ("BIGGEST", "dollars"),
        ("Newest", "time"),
        # Unrecognized values pass through for caller fallback.
        ("bogus", "bogus"),
        ("", ""),
    ],
)
def test_normalize_sort_by(alias: str, expected: str) -> None:
    """Translate sort aliases to canonical sort keys."""
    assert normalize_sort_by(alias) == expected
