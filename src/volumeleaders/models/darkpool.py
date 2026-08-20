"""Dark pool price-volume distribution models."""

from __future__ import annotations

from pydantic import Field

from volumeleaders.models.base import AspNetDate, VLBaseModel


class DarkPoolVolumeBin(VLBaseModel):
    """Price bin record from a multi-week dark pool volume report."""

    ticker: str = Field(alias="Ticker")
    bin_id: int = Field(alias="BinID")
    week_number: int = Field(alias="WeekNumber")
    week_start: AspNetDate = Field(alias="WeekStart")
    range_min_price: float = Field(alias="RangeMinPrice")
    range_max_price: float = Field(alias="RangeMaxPrice")
    bin_width: float = Field(alias="BinWidth")
    bin_low: float = Field(alias="BinLow")
    bin_high: float = Field(alias="BinHigh")
    dp_dollars: float = Field(alias="DPDollars")
    last_close: float = Field(alias="LastClose")
