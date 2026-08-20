"""Endpoints for sector breakdown, outliers, themes, supply/demand, and daily returns."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING
from urllib.parse import urlencode

from volumeleaders._parsing import format_datekey
from volumeleaders.models import (
    InstitutionalOutlier,
    SectorBreakdown,
    SectorDailyReturn,
    SectorThemeNotional,
    SupplyDemandArea,
)

if TYPE_CHECKING:
    from volumeleaders._client import VolumeLeadersClient

_DATE_KEY_LENGTH = 8


def _to_date_key(value: str) -> str:
    """Normalize YYYY-MM-DD or YYYYMMDD strings to YYYYMMDD."""
    stripped = value.strip()
    if len(stripped) == _DATE_KEY_LENGTH and stripped.isdigit():
        return stripped
    return format_datekey(datetime.fromisoformat(stripped))


def get_sector_breakdown(
    client: VolumeLeadersClient,
    *,
    start_date: str = "",
    end_date: str = "",
) -> list[SectorBreakdown]:
    """Return daily institutional dollar volume breakdown by sector."""
    payload = {
        "StartDateKey": _to_date_key(start_date) if start_date else "",
        "EndDateKey": _to_date_key(end_date) if end_date else "",
    }
    response = client.post_json("/SectorBreakdown/GetSectorBreakdown", payload)
    rows = response if isinstance(response, list) else []
    return [SectorBreakdown.model_validate(row) for row in rows]


def get_institutional_outliers(
    client: VolumeLeadersClient,
    *,
    end_date: str = "",
    lookback_days: int = 7,
    min_std: float = 2.0,
) -> list[InstitutionalOutlier]:
    """Return statistical outlier block trade records exceeding standard deviation threshold."""
    payload = {
        "EndDate": end_date,
        "LookbackDays": lookback_days,
        "MinSTD": min_std,
    }
    response = client.post_json("/SectorBreakdown/GetInstitutionalOutliers", payload)
    rows = response if isinstance(response, list) else []
    return [InstitutionalOutlier.model_validate(row) for row in rows]


def get_notional_by_sector_by_name(
    client: VolumeLeadersClient,
    *,
    end_date: str = "",
    top_themes: int = 10,
    top_tickers: int = 10,
) -> list[SectorThemeNotional]:
    """Return hierarchical sector, theme, and ticker institutional capital allocation."""
    payload = {
        "EndDateKey": int(_to_date_key(end_date)) if end_date else 0,
        "TopThemes": top_themes,
        "TopTickers": top_tickers,
    }
    response = client.post_json(
        "/SectorBreakdown/GetNotionalBySectorByName",
        payload,
    )
    rows = response if isinstance(response, list) else []
    return [SectorThemeNotional.model_validate(row) for row in rows]


def get_supply_demand_areas(
    client: VolumeLeadersClient,
    *,
    start_date: str = "",
    end_date: str = "",
) -> list[SupplyDemandArea]:
    """Return automated sector supply and demand level distribution statistics."""
    payload = {
        "StartDateKey": int(_to_date_key(start_date)) if start_date else 0,
        "EndDateKey": int(_to_date_key(end_date)) if end_date else 0,
    }
    response = client.post_json(
        "/SectorBreakdown/GetAutomatedSupplyAndDemandAreas",
        payload,
    )
    rows = response if isinstance(response, list) else []
    return [SupplyDemandArea.model_validate(row) for row in rows]


def get_sector_daily_returns(
    client: VolumeLeadersClient,
    *,
    start_date: str = "",
    end_date: str = "",
) -> list[SectorDailyReturn]:
    """Return multi-factor sector performance, momentum, risk, and benchmark metrics."""
    body = urlencode({"StartDate": start_date, "EndDate": end_date})
    response = client.post_form(
        "/SectorBreakdown/GetSectorDailyReturns",
        body,
    )
    rows = response if isinstance(response, list) else []
    return [SectorDailyReturn.model_validate(row) for row in rows]
