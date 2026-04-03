"""Endpoint for earnings calendar data."""

from __future__ import annotations

from volumeleaders._client import VolumeLeadersClient
from volumeleaders._datatables import DataTablesRequest
from volumeleaders.models import Earnings

EARNINGS_COLUMNS = [
    "Date",
    "Ticker",
    "Current",
    "Sector",
    "Industry",
    "TradeCount",
    "TradeClusterCount",
    "TradeClusterBombCount",
    "Ticker",
]


def get_earnings(
    client: VolumeLeadersClient, *, start_date: str, end_date: str
) -> list[Earnings]:
    """Return earnings rows within a date range."""
    request = DataTablesRequest(
        columns=EARNINGS_COLUMNS,
        start=0,
        length=-1,
        order_column_index=0,
        order_direction="asc",
        custom_filters={"StartDate": start_date, "EndDate": end_date},
    )
    rows = client.post_datatables("/Earnings/GetEarnings", request.encode())
    return [Earnings.model_validate(row) for row in rows]
