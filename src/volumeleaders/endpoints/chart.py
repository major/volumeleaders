"""Endpoints for chart data, snapshots, and company metadata."""

from __future__ import annotations

from datetime import datetime

from volumeleaders._client import VolumeLeadersClient
from volumeleaders._datatables import DataTablesRequest
from volumeleaders._parsing import format_datekey
from volumeleaders.endpoints.levels import TRADE_LEVEL_COLUMNS
from volumeleaders.models import (
    Company,
    PriceBar,
    Snapshot,
    SnapshotResponse,
    TradeLevel,
)


def _to_date_key(value: str) -> str:
    """Normalize YYYY-MM-DD or YYYYMMDD strings to YYYYMMDD."""
    stripped = value.strip()
    if len(stripped) == 8 and stripped.isdigit():
        return stripped
    return format_datekey(datetime.fromisoformat(stripped))


def get_price_data(
    client: VolumeLeadersClient,
    *,
    ticker: str,
    start_date: str,
    end_date: str,
    volume_profile: int = 0,
    levels: int = 5,
    min_volume: int = 0,
    max_volume: int = 2_000_000_000,
    min_dollars: float = 500_000,
    max_dollars: float = 30_000_000_000,
    dark_pools: int = -1,
    sweeps: int = -1,
    late_prints: int = -1,
    signature_prints: int = -1,
    trade_count: int = 3,
    min_price: float = 0,
    max_price: float = 100_000,
    vcd: int = 0,
    trade_rank: int = -1,
    trade_rank_snapshot: int = -1,
    include_premarket: int = 1,
    include_rth: int = 1,
    include_ah: int = 1,
    include_opening: int = 1,
    include_closing: int = 1,
    include_phantom: int = 1,
    include_offsetting: int = 1,
) -> list[PriceBar]:
    """Return one-minute chart bars and metadata for a ticker/date range."""
    payload = {
        "StartDateKey": _to_date_key(start_date),
        "EndDateKey": _to_date_key(end_date),
        "Ticker": ticker,
        "VolumeProfile": volume_profile,
        "Levels": levels,
        "MinVolume": min_volume,
        "MaxVolume": max_volume,
        "MinDollars": min_dollars,
        "MaxDollars": max_dollars,
        "DarkPools": dark_pools,
        "Sweeps": sweeps,
        "LatePrints": late_prints,
        "SignaturePrints": signature_prints,
        "TradeCount": trade_count,
        "MinPrice": min_price,
        "MaxPrice": max_price,
        "VCD": vcd,
        "TradeRank": trade_rank,
        "TradeRankSnapshot": trade_rank_snapshot,
        "IncludePremarket": include_premarket,
        "IncludeRTH": include_rth,
        "IncludeAH": include_ah,
        "IncludeOpening": include_opening,
        "IncludeClosing": include_closing,
        "IncludePhantom": include_phantom,
        "IncludeOffsetting": include_offsetting,
    }
    response = client.post_json("/Chart0/GetAllPriceVolumeTradeData", payload)
    rows = response[0] if isinstance(response, list) and response else []
    return [PriceBar.model_validate(row) for row in rows]


def get_snapshot(
    client: VolumeLeadersClient, *, ticker: str, date_key: str
) -> Snapshot:
    """Return quote snapshot envelope for a ticker/date key."""
    payload = {"Ticker": ticker, "DateKey": _to_date_key(date_key)}
    response = client.post_json("/Chart0/GetSnapshot", payload)
    return SnapshotResponse.model_validate(response).snapshot


def get_company(client: VolumeLeadersClient, *, ticker: str) -> Company:
    """Return company metadata for a single ticker."""
    payload = {"Ticker": ticker}
    response = client.post_json("/Chart0/GetCompany", payload)
    return Company.model_validate(response)


def get_chart_levels(
    client: VolumeLeadersClient,
    *,
    ticker: str,
    start_date: str,
    end_date: str,
    levels: int = 5,
) -> list[TradeLevel]:
    """Return chart-level overlays for a ticker/date range."""
    request = DataTablesRequest(
        columns=TRADE_LEVEL_COLUMNS,
        start=0,
        length=-1,
        order_column_index=0,
        order_direction="desc",
        custom_filters={
            "StartDate": start_date,
            "EndDate": end_date,
            "Ticker": ticker,
            "Levels": levels,
        },
    )
    rows = client.post_datatables("/Chart0/GetTradeLevels", request.encode())
    return [TradeLevel.model_validate(row) for row in rows]
