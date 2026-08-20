"""Model validation tests for dark pool payloads."""

from importlib import import_module
from typing import Any

DarkPoolVolumeBin = import_module("volumeleaders.models").DarkPoolVolumeBin


def test_dark_pool_volume_bin_model(
    sample_dark_pool_volume_report_response: list[dict[str, Any]],
) -> None:
    """Validate DarkPoolVolumeBin model parses real response rows."""
    assert len(sample_dark_pool_volume_report_response) > 0
    row = DarkPoolVolumeBin.model_validate(
        sample_dark_pool_volume_report_response[0],
    )
    assert row.ticker == "AAPL"
    assert row.bin_id == 1
    assert row.week_number == 1
    assert row.week_start is not None
    assert row.range_min_price > 0
    assert row.range_max_price >= row.range_min_price
    assert row.bin_low > 0
    assert row.bin_high >= row.bin_low
    assert row.dp_dollars >= 0
    assert row.last_close > 0
