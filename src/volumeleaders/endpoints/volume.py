"""Endpoints for institutional and total volume leaderboards."""

from __future__ import annotations

from volumeleaders._client import VolumeLeadersClient
from volumeleaders._datatables import DataTablesRequest
from volumeleaders.models import InstitutionalVolume, TotalVolume

INSTITUTIONAL_VOLUME_COLUMNS = [
    "Ticker",
    "Ticker",
    "Price",
    "Sector",
    "Industry",
    "Volume",
    "TotalInstitutionalDollars",
    "TotalInstitutionalDollarsRank",
    "LastComparibleTradeDate",
    "LastComparibleTradeDate",
]

TOTAL_VOLUME_COLUMNS = [
    "Ticker",
    "Ticker",
    "Price",
    "Sector",
    "Industry",
    "Volume",
    "TotalDollars",
    "TotalDollarsRank",
    "LastComparibleTradeDate",
    "LastComparibleTradeDate",
]


def _get_institutional_volume(
    client: VolumeLeadersClient,
    path: str,
    *,
    date: str,
    tickers: str = "",
    start: int = 0,
    length: int = 100,
) -> list[InstitutionalVolume]:
    """Shared implementation for institutional volume endpoints."""
    request = DataTablesRequest(
        columns=INSTITUTIONAL_VOLUME_COLUMNS,
        start=start,
        length=length,
        order_column_index=1,
        order_direction="asc",
        custom_filters={"Date": date, "Tickers": tickers},
    )
    rows = client.post_datatables(path, request.encode())
    return [InstitutionalVolume.model_validate(row) for row in rows]


def get_institutional_volume(
    client: VolumeLeadersClient,
    *,
    date: str,
    tickers: str = "",
    start: int = 0,
    length: int = 100,
) -> list[InstitutionalVolume]:
    """Return institutional volume leaderboard rows for a date."""
    return _get_institutional_volume(
        client,
        "/InstitutionalVolume/GetInstitutionalVolume",
        date=date,
        tickers=tickers,
        start=start,
        length=length,
    )


def get_ah_institutional_volume(
    client: VolumeLeadersClient,
    *,
    date: str,
    tickers: str = "",
    start: int = 0,
    length: int = 100,
) -> list[InstitutionalVolume]:
    """Return after-hours institutional volume leaderboard rows for a date."""
    return _get_institutional_volume(
        client,
        "/AHInstitutionalVolume/GetAHInstitutionalVolume",
        date=date,
        tickers=tickers,
        start=start,
        length=length,
    )


def get_total_volume(
    client: VolumeLeadersClient,
    *,
    date: str,
    tickers: str = "",
    start: int = 0,
    length: int = 100,
) -> list[TotalVolume]:
    """Return total volume leaderboard rows for a date."""
    request = DataTablesRequest(
        columns=TOTAL_VOLUME_COLUMNS,
        start=start,
        length=length,
        order_column_index=1,
        order_direction="asc",
        custom_filters={"Date": date, "Tickers": tickers},
    )
    rows = client.post_datatables("/TotalVolume/GetTotalVolume", request.encode())
    return [TotalVolume.model_validate(row) for row in rows]
