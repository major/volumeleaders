"""Model validation tests for volume leaderboard payloads."""

from importlib import import_module
from typing import Any

InstitutionalVolume = import_module("volumeleaders.models").InstitutionalVolume


def test_institutional_volume_model_validates_real_response(
    sample_institutional_volume_response: dict[str, Any],
) -> None:
    """Validate InstitutionalVolume model from real leaderboard row."""
    row = sample_institutional_volume_response["data"][0]
    volume = InstitutionalVolume.model_validate(row)

    assert volume.total_institutional_dollars > 0
    assert volume.total_institutional_dollars_rank > 0
