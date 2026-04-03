"""Endpoints for watch list tickers and saved watch list configs."""

from __future__ import annotations

from volumeleaders._client import VolumeLeadersClient
from volumeleaders._datatables import DataTablesRequest
from volumeleaders.models import WatchListConfig, WatchListTicker

WATCHLIST_TICKER_COLUMNS = [
    "Ticker",
    "Price",
    "NearestTop10TradeDate",
    "NearestTop10TradeClusterDate",
    "NearestTop10TradeLevel",
    "Charts",
]

WATCHLIST_CONFIG_COLUMNS = ["Name", "Name", "Tickers", "Criteria"]


def get_watchlist_tickers(
    client: VolumeLeadersClient, *, watchlist_key: int = -1
) -> list[WatchListTicker]:
    """Return tickers for a selected watch list."""
    request = DataTablesRequest(
        columns=WATCHLIST_TICKER_COLUMNS,
        start=0,
        length=-1,
        order_column_index=0,
        order_direction="asc",
        custom_filters={"WatchListKey": watchlist_key},
    )
    rows = client.post_datatables("/WatchLists/GetWatchListTickers", request.encode())
    return [WatchListTicker.model_validate(row) for row in rows]


def get_watchlist_configs(client: VolumeLeadersClient) -> list[WatchListConfig]:
    """Return saved watch list template configurations."""
    request = DataTablesRequest(
        columns=WATCHLIST_CONFIG_COLUMNS,
        start=0,
        length=-1,
        order_column_index=1,
        order_direction="asc",
    )
    rows = client.post_datatables("/WatchListConfigs/GetWatchLists", request.encode())
    return [WatchListConfig.model_validate(row) for row in rows]
