"""Model validation tests for exhaustion score payloads."""

from importlib import import_module
from typing import Any

ExhaustionScore = import_module("volumeleaders.models").ExhaustionScore


def test_exhaustion_score_model_validates_real_response(
    sample_exhaustion_response: dict[str, Any],
) -> None:
    """Validate ExhaustionScore model fields are positive rank integers."""
    score = ExhaustionScore.model_validate(sample_exhaustion_response)

    assert score.exhaustion_score_rank > 0
    assert score.exhaustion_score_rank_30_day > 0
    assert score.exhaustion_score_rank_90_day > 0
    assert score.exhaustion_score_rank_365_day > 0
