"""Model validation tests for trade-related models."""

from datetime import datetime
from importlib import import_module
from typing import Any

_models = import_module("volumeleaders.models")
Trade = _models.Trade
TradeCluster = _models.TradeCluster
TradeClusterBomb = _models.TradeClusterBomb


def test_trade_model_validates_real_trade_response(
    sample_trade_response: dict[str, Any],
) -> None:
    """Validate Trade model against a real trades API row."""
    row = sample_trade_response["data"][0]
    trade = Trade.model_validate(row)

    assert trade.ticker == "SPY"
    assert trade.trade_rank == 9999
    assert trade.dark_pool
    assert trade.dollars > 0
    assert isinstance(trade.last_comparible_trade_date, datetime)


def test_trade_cluster_model_validates_real_cluster_response(
    sample_trade_cluster_response: dict[str, Any],
) -> None:
    """Validate TradeCluster model against a real cluster API row."""
    row = sample_trade_cluster_response["data"][0]
    cluster = TradeCluster.model_validate(row)

    assert cluster.trade_count > 0
    assert cluster.trade_cluster_rank == 9999
    assert "T" in cluster.min_full_date_time
    assert "T" in cluster.max_full_date_time


def test_trade_cluster_bomb_model_validates_real_bomb_response(
    sample_trade_cluster_bomb_response: dict[str, Any],
) -> None:
    """Validate TradeClusterBomb model against a real bomb API row."""
    row = sample_trade_cluster_bomb_response["data"][0]
    bomb = TradeClusterBomb.model_validate(row)

    assert bomb.ticker == "NVS"
    assert bomb.trade_count > 0
    assert bomb.trade_cluster_bomb_rank == 2
    assert bomb.dollars > 0
    assert isinstance(bomb.last_comparable_trade_cluster_bomb_date, datetime)
    assert "T" in bomb.min_full_date_time
    assert "T" in bomb.max_full_date_time
