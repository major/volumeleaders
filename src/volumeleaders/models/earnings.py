"""Earnings endpoint response models."""

from pydantic import Field

from volumeleaders.models.base import AspNetDate, VLBaseModel


class Earnings(VLBaseModel):
    """Upcoming or recent earnings row with related trade activity counts."""

    ticker: str = Field(alias="Ticker")
    name: str = Field(alias="Name")
    sector: str | None = Field(alias="Sector")
    industry: str | None = Field(alias="Industry")
    earnings_date: AspNetDate = Field(alias="EarningsDate")
    after_market_close: bool = Field(alias="AfterMarketClose")
    trade_count: int = Field(alias="TradeCount")
    trade_cluster_count: int = Field(alias="TradeClusterCount")
    trade_cluster_bomb_count: int = Field(alias="TradeClusterBombCount")
