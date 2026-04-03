"""Tests for exhaustion endpoint helper functions."""

from importlib import import_module
from typing import Any
from unittest.mock import Mock

get_exhaustion_scores = import_module(
    "volumeleaders.endpoints.exhaustion"
).get_exhaustion_scores


def test_get_exhaustion_scores_returns_typed_model(
    sample_exhaustion_response: dict[str, Any],
) -> None:
    """Validate endpoint transforms JSON payload into ExhaustionScore model."""
    client = Mock()
    client.post_json.return_value = sample_exhaustion_response

    score = get_exhaustion_scores(client)

    assert score.exhaustion_score_rank > 0
    assert score.exhaustion_score_rank_30_day > 0
    assert score.exhaustion_score_rank_90_day > 0
    assert score.exhaustion_score_rank_365_day > 0
