"""Endpoints for trade levels and level-touch events."""

from __future__ import annotations

from volumeleaders._client import VolumeLeadersClient
from volumeleaders._datatables import DataTablesRequest
from volumeleaders.models import TradeLevel, TradeLevelTouch

TRADE_LEVEL_COLUMNS = [
    "Price",
    "Dollars",
    "Volume",
    "Trades",
    "RelativeSize",
    "CumulativeDistribution",
    "TradeLevelRank",
    "Level Date Range",
]

TRADE_LEVEL_TOUCH_COLUMNS = [
    "FullDateTime",
    "Ticker",
    "Sector",
    "Industry",
    "Dollars",
    "Volume",
    "Trades",
    "Price",
    "RelativeSize",
    "CumulativeDistribution",
    "TradeLevelRank",
    "TradeLevelTouches",
    "Dates",
]


def get_trade_levels(
    client: VolumeLeadersClient,
    *,
    ticker: str,
    start_date: str,
    end_date: str,
    min_volume: int = 0,
    max_volume: int = 2_000_000_000,
    min_price: float = 0,
    max_price: float = 100_000,
    min_dollars: float = 500_000,
    max_dollars: float = 30_000_000_000,
    vcd: int = 0,
    relative_size: int = 0,
    trade_level_rank: int = -1,
    trade_level_count: int = 10,
) -> list[TradeLevel]:
    """Return significant price levels for a single ticker."""
    request = DataTablesRequest(
        columns=TRADE_LEVEL_COLUMNS,
        start=0,
        length=-1,
        order_column_index=1,
        order_direction="desc",
        custom_filters={
            "Ticker": ticker,
            "MinVolume": min_volume,
            "MaxVolume": max_volume,
            "MinPrice": min_price,
            "MaxPrice": max_price,
            "MinDollars": min_dollars,
            "MaxDollars": max_dollars,
            "VCD": vcd,
            "RelativeSize": relative_size,
            "MinDate": start_date,
            "MaxDate": end_date,
            "TradeLevelRank": trade_level_rank,
            "TradeLevelCount": trade_level_count,
        },
    )
    rows = client.post_datatables("/TradeLevels/GetTradeLevels", request.encode())
    return [TradeLevel.model_validate(row) for row in rows]


def get_trade_level_touches(
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
    vcd: int = 0,
    relative_size: int = 0,
    trade_level_rank: int = 10,
    start: int = 0,
    length: int = 100,
) -> list[TradeLevelTouch]:
    """Return level-touch events across one or many tickers."""
    request = DataTablesRequest(
        columns=TRADE_LEVEL_TOUCH_COLUMNS,
        start=start,
        length=length,
        order_column_index=0,
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
            "RelativeSize": relative_size,
            "TradeLevelRank": trade_level_rank,
        },
    )
    rows = client.post_datatables(
        "/TradeLevelTouches/GetTradeLevelTouches", request.encode()
    )
    return [TradeLevelTouch.model_validate(row) for row in rows]
