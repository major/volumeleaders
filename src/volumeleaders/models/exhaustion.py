"""Exhaustion score response models."""

from pydantic import Field

from volumeleaders.models.base import VLBaseModel


class ExhaustionScore(VLBaseModel):
    """Exhaustion score rank values for a specific trading day."""

    date_key: int = Field(alias="DateKey")
    exhaustion_score_rank: int = Field(alias="ExhaustionScoreRank")
    exhaustion_score_rank_30_day: int = Field(alias="ExhaustionScoreRank30Day")
    exhaustion_score_rank_90_day: int = Field(alias="ExhaustionScoreRank90Day")
    exhaustion_score_rank_365_day: int = Field(alias="ExhaustionScoreRank365Day")
