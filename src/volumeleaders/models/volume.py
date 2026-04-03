"""Volume leaderboard response models."""

from volumeleaders.models.trades import Trade


class InstitutionalVolume(Trade):
    """Institutional volume leaderboard row."""


class TotalVolume(Trade):
    """Total volume leaderboard row."""
