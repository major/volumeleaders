"""Endpoints for trades, clusters, and snapshot maps."""

from __future__ import annotations

from volumeleaders._client import VolumeLeadersClient
from volumeleaders._datatables import DataTablesRequest
from volumeleaders._parsing import parse_snapshot_string
from volumeleaders.models import Trade, TradeCluster, TradeClusterBomb

TRADE_COLUMNS = [
    "FullTimeString24",
    "FullTimeString24",
    "Ticker",
    "Current",
    "Trade",
    "Sector",
    "Industry",
    "Volume",
    "Dollars",
    "DollarsMultiplier",
    "CumulativeDistribution",
    "TradeRank",
    "LastComparibleTradeDate",
    "LastComparibleTradeDate",
]

TRADE_CLUSTER_COLUMNS = [
    "MinFullTimeString24",
    "MinFullTimeString24",
    "Ticker",
    "TradeCount",
    "Current",
    "Cluster",
    "Sector",
    "Industry",
    "Volume",
    "Dollars",
    "DollarsMultiplier",
    "CumulativeDistribution",
    "TradeClusterRank",
    "LastComparibleTradeClusterDate",
    "LastComparibleTradeClusterDate",
]

TRADE_CLUSTER_BOMB_COLUMNS = [
    "MinFullTimeString24",
    "MinFullTimeString24",
    "Ticker",
    "TradeCount",
    "Sector",
    "Industry",
    "Volume",
    "Dollars",
    "DollarsMultiplier",
    "CumulativeDistribution",
    "TradeClusterBombRank",
    "LastComparableTradeClusterBombDate",
    "LastComparableTradeClusterBombDate",
]


def get_trades(
    client: VolumeLeadersClient,
    *,
    tickers: str = "",
    start_date: str,
    end_date: str,
    min_volume: int = 0,
    max_volume: int = 2_000_000_000,
    min_price: float = 0,
    max_price: float = 100_000,
    min_dollars: float = 500_000,
    max_dollars: float = 30_000_000_000,
    conditions: int = -1,
    vcd: int = 0,
    security_type_key: int = -1,
    relative_size: int = 5,
    dark_pools: int = -1,
    sweeps: int = -1,
    late_prints: int = -1,
    signature_prints: int = -1,
    even_shared: int = -1,
    trade_rank: int = -1,
    trade_rank_snapshot: int = -1,
    market_cap: int = 0,
    include_premarket: int = 1,
    include_rth: int = 1,
    include_ah: int = 1,
    include_opening: int = 1,
    include_closing: int = 1,
    include_phantom: int = 1,
    include_offsetting: int = 1,
    sector_industry: str = "",
    start: int = 0,
    length: int = 100,
    order_column_index: int = 1,
    order_direction: str = "desc",
) -> list[Trade]:
    """Return trades from the main trades endpoint."""
    request = DataTablesRequest(
        columns=TRADE_COLUMNS,
        start=start,
        length=length,
        order_column_index=order_column_index,
        order_direction=order_direction,
        custom_filters={
            "Tickers": tickers,
            "StartDate": start_date,
            "EndDate": end_date,
            "MinVolume": min_volume,
            "MaxVolume": max_volume,
            "MinPrice": min_price,
            "MaxPrice": max_price,
            "MinDollars": min_dollars,
            "MaxDollars": max_dollars,
            "Conditions": conditions,
            "VCD": vcd,
            "SecurityTypeKey": security_type_key,
            "RelativeSize": relative_size,
            "DarkPools": dark_pools,
            "Sweeps": sweeps,
            "LatePrints": late_prints,
            "SignaturePrints": signature_prints,
            "EvenShared": even_shared,
            "TradeRank": trade_rank,
            "TradeRankSnapshot": trade_rank_snapshot,
            "MarketCap": market_cap,
            "IncludePremarket": include_premarket,
            "IncludeRTH": include_rth,
            "IncludeAH": include_ah,
            "IncludeOpening": include_opening,
            "IncludeClosing": include_closing,
            "IncludePhantom": include_phantom,
            "IncludeOffsetting": include_offsetting,
            "SectorIndustry": sector_industry,
        },
    )
    rows = client.post_datatables("/Trades/GetTrades", request.encode())
    return [Trade.model_validate(row) for row in rows]


def get_trade_clusters(
    client: VolumeLeadersClient,
    *,
    tickers: str = "",
    start_date: str,
    end_date: str,
    min_volume: int = 0,
    max_volume: int = 2_000_000_000,
    min_price: float = 0,
    max_price: float = 100_000,
    min_dollars: float = 10_000_000,
    max_dollars: float = 30_000_000_000,
    vcd: int = 0,
    security_type_key: int = -1,
    relative_size: int = 5,
    trade_cluster_rank: int = -1,
    sector_industry: str = "",
    start: int = 0,
    length: int = 1000,
) -> list[TradeCluster]:
    """Return aggregated trade clusters."""
    request = DataTablesRequest(
        columns=TRADE_CLUSTER_COLUMNS,
        start=start,
        length=length,
        order_column_index=1,
        order_direction="desc",
        custom_filters={
            "Tickers": tickers,
            "StartDate": start_date,
            "EndDate": end_date,
            "MinVolume": min_volume,
            "MaxVolume": max_volume,
            "MinPrice": min_price,
            "MaxPrice": max_price,
            "MinDollars": min_dollars,
            "MaxDollars": max_dollars,
            "VCD": vcd,
            "SecurityTypeKey": security_type_key,
            "RelativeSize": relative_size,
            "TradeClusterRank": trade_cluster_rank,
            "SectorIndustry": sector_industry,
        },
    )
    rows = client.post_datatables("/TradeClusters/GetTradeClusters", request.encode())
    return [TradeCluster.model_validate(row) for row in rows]


def get_trade_cluster_bombs(
    client: VolumeLeadersClient,
    *,
    tickers: str = "",
    start_date: str,
    end_date: str,
    min_volume: int = 0,
    max_volume: int = 2_000_000_000,
    min_dollars: float = 0,
    max_dollars: float = 30_000_000_000,
    vcd: int = 0,
    security_type_key: int = 0,
    relative_size: int = 0,
    trade_cluster_bomb_rank: int = -1,
    sector_industry: str = "",
    start: int = 0,
    length: int = 100,
) -> list[TradeClusterBomb]:
    """Return trade cluster bomb rows."""
    request = DataTablesRequest(
        columns=TRADE_CLUSTER_BOMB_COLUMNS,
        start=start,
        length=length,
        order_column_index=1,
        order_direction="desc",
        custom_filters={
            "Tickers": tickers,
            "StartDate": start_date,
            "EndDate": end_date,
            "MinVolume": min_volume,
            "MaxVolume": max_volume,
            "MinDollars": min_dollars,
            "MaxDollars": max_dollars,
            "VCD": vcd,
            "SecurityTypeKey": security_type_key,
            "RelativeSize": relative_size,
            "TradeClusterBombRank": trade_cluster_bomb_rank,
            "SectorIndustry": sector_industry,
        },
    )
    rows = client.post_datatables(
        "/TradeClusterBombs/GetTradeClusterBombs", request.encode()
    )
    return [TradeClusterBomb.model_validate(row) for row in rows]


def get_all_snapshots(client: VolumeLeadersClient) -> dict[str, float]:
    """Return ticker-to-price snapshot map for all symbols."""
    response = client.post_json("/Trades/GetAllSnapshots", {})
    raw = response if isinstance(response, str) else ""
    return parse_snapshot_string(raw)
