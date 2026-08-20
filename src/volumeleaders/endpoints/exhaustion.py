"""Endpoints for exhaustion score data."""

from __future__ import annotations

from typing import TYPE_CHECKING

from volumeleaders.models import ExhaustionScore

if TYPE_CHECKING:
    from volumeleaders._client import VolumeLeadersClient


def get_exhaustion_scores(
    client: VolumeLeadersClient,
    date: str = "",
) -> ExhaustionScore:
    """Return exhaustion score ranks for a given date.

    Args:
        client: Authenticated VolumeLeaders client instance.
        date: Date in ``YYYY-MM-DD`` format, empty string means current day.

    Returns:
        Exhaustion score model for the requested day.

    """
    payload = {"Date": date}
    response = client.post_json("/ExecutiveSummary/GetExhaustionScores", payload)
    return ExhaustionScore.model_validate(response)
