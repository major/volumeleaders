"""Model validation tests for trade level touch payloads."""

from importlib import import_module
from typing import Any

TradeLevelTouch = import_module("volumeleaders.models").TradeLevelTouch


def test_trade_level_touch_model_validates_real_response(
    sample_trade_level_touch_response: dict[str, Any],
) -> None:
    """Validate TradeLevelTouch model from real touch row."""
    row = sample_trade_level_touch_response["data"][0]
    touch = TradeLevelTouch.model_validate(row)

    assert touch.trade_level_rank > 0
    assert touch.price > 0
    assert touch.ticker == "WTID"
