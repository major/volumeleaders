"""Tests for trade endpoint helper functions."""

import json
from importlib import import_module
from typing import Any
from unittest.mock import Mock

_trades = import_module("volumeleaders.endpoints.trades")
_models = import_module("volumeleaders.models")
get_all_snapshots = _trades.get_all_snapshots
get_trades = _trades.get_trades
get_trade_clusters = _trades.get_trade_clusters
get_trade_cluster_bombs = _trades.get_trade_cluster_bombs
Trade = _models.Trade
TradeCluster = _models.TradeCluster
TradeClusterBomb = _models.TradeClusterBomb


def test_get_trades_returns_typed_trade_models(
    sample_trade_response: dict[str, Any],
) -> None:
    """Return a Trade model list from DataTables row payloads."""
    client = Mock()
    client.post_datatables.return_value = sample_trade_response["data"]

    trades = get_trades(
        client,
        start_date="2026-04-01",
        end_date="2026-04-01",
    )

    assert len(trades) == len(sample_trade_response["data"])
    assert all(isinstance(item, Trade) for item in trades)
    assert trades[0].ticker == "SPY"


def test_get_trade_clusters_returns_typed_models(
    sample_trade_cluster_response: dict[str, Any],
) -> None:
    """Return a TradeCluster model list from DataTables row payloads."""
    client = Mock()
    client.post_datatables.return_value = sample_trade_cluster_response["data"]

    clusters = get_trade_clusters(
        client,
        start_date="2026-04-01",
        end_date="2026-04-01",
    )

    assert len(clusters) == len(sample_trade_cluster_response["data"])
    assert all(isinstance(item, TradeCluster) for item in clusters)
    assert clusters[0].ticker == "SPY"


def test_get_trade_cluster_bombs_returns_typed_models(
    sample_trade_cluster_bomb_response: dict[str, Any],
) -> None:
    """Return a TradeClusterBomb model list from DataTables row payloads."""
    client = Mock()
    client.post_datatables.return_value = sample_trade_cluster_bomb_response["data"]

    bombs = get_trade_cluster_bombs(
        client,
        start_date="2026-04-02",
        end_date="2026-04-02",
    )

    assert len(bombs) == len(sample_trade_cluster_bomb_response["data"])
    assert all(isinstance(item, TradeClusterBomb) for item in bombs)
    assert bombs[0].ticker == "NVS"


def test_get_all_snapshots_parses_raw_snapshot_string(
    sample_snapshot_string: str,
) -> None:
    """Parse ticker-price mapping from the raw all-snapshots response string."""
    client = Mock()
    client.post_json.return_value = json.loads(sample_snapshot_string)

    snapshots = get_all_snapshots(client)

    assert snapshots["SPY"] > 0
    assert snapshots["AAPL"] > 0
