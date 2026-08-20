"""Model validation tests for watchlist configuration payloads."""

from importlib import import_module
from typing import Any

WatchListConfig = import_module("volumeleaders.models").WatchListConfig

_MIN_DOLLARS = 10_000_000


def test_watchlist_config_model_validates_real_response(
    sample_watchlist_config_response: dict[str, Any],
) -> None:
    """Validate WatchListConfig model from real saved config row."""
    row = sample_watchlist_config_response["data"][0]
    config = WatchListConfig.model_validate(row)

    assert config.name == "BigOnes"
    assert config.min_dollars == _MIN_DOLLARS
    assert config.dark_pools
