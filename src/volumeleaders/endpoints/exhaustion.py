"""Endpoints for exhaustion score data."""

from __future__ import annotations

from volumeleaders._client import VolumeLeadersClient
from volumeleaders.models import ExhaustionScore


def get_exhaustion_scores(
    client: VolumeLeadersClient, date: str = ""
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
