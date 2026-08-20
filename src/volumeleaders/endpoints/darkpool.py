"""Endpoints for dark pool volume profile reports."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from volumeleaders._parsing import format_datekey
from volumeleaders.models import DarkPoolVolumeBin

if TYPE_CHECKING:
    from volumeleaders._client import VolumeLeadersClient

_DATE_KEY_LENGTH = 8


def _to_date_key(value: str) -> str:
    """Normalize YYYY-MM-DD or YYYYMMDD strings to YYYYMMDD."""
    stripped = value.strip()
    if len(stripped) == _DATE_KEY_LENGTH and stripped.isdigit():
        return stripped
    return format_datekey(datetime.fromisoformat(stripped))


def get_dark_pool_volume_report(
    client: VolumeLeadersClient,
    *,
    last_trade_date: str = "",
    start_date: str = "",
    end_date: str = "",
    bins: int = 24,
    tickers: str = "",
) -> list[DarkPoolVolumeBin]:
    """Return dark pool price-bin volume distribution report for specified tickers."""
    payload = {
        "LastTradeDate": last_trade_date or end_date,
        "StartDateKey": _to_date_key(start_date) if start_date else "",
        "EndDateKey": _to_date_key(end_date) if end_date else "",
        "Bins": bins,
        "Tickers": tickers,
    }
    response = client.post_json(
        "/SectorBreakdown/GetDarkPoolVolumeReport",
        payload,
    )
    rows = response if isinstance(response, list) else []
    return [DarkPoolVolumeBin.model_validate(row) for row in rows]
