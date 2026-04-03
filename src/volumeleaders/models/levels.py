"""Trade level and level-touch response models."""

from pydantic import Field

from volumeleaders.models.base import AspNetDate, VLBaseModel


class TradeLevel(VLBaseModel):
    """Price level aggregate data for a ticker."""

    ticker: str | None = Field(alias="Ticker")
    name: str | None = Field(alias="Name")
    price: float = Field(alias="Price")
    dollars: float = Field(alias="Dollars")
    volume: int = Field(alias="Volume")
    trades: int = Field(alias="Trades")
    relative_size: float = Field(alias="RelativeSize")
    cumulative_distribution: float = Field(alias="CumulativeDistribution")
    trade_level_rank: int = Field(alias="TradeLevelRank")
    min_date: AspNetDate = Field(alias="MinDate")
    max_date: AspNetDate = Field(alias="MaxDate")
    dates: str = Field(alias="Dates")


class TradeLevelTouch(VLBaseModel):
    """Trade event representing touches at a notable price level."""

    ticker: str = Field(alias="Ticker")
    sector: str | None = Field(alias="Sector")
    industry: str | None = Field(alias="Industry")
    name: str = Field(alias="Name")
    date: AspNetDate = Field(alias="Date")
    min_date: AspNetDate = Field(alias="MinDate")
    max_date: AspNetDate = Field(alias="MaxDate")
    full_date_time: str = Field(alias="FullDateTime")
    full_time_string24: str | None = Field(alias="FullTimeString24")
    dates: str = Field(alias="Dates")
    price: float = Field(alias="Price")
    dollars: float = Field(alias="Dollars")
    volume: int = Field(alias="Volume")
    trades: int = Field(alias="Trades")
    cumulative_distribution: float = Field(alias="CumulativeDistribution")
    trade_level_rank: int = Field(alias="TradeLevelRank")
    total_rows: int = Field(alias="TotalRows")
    trade_level_touches: int = Field(alias="TradeLevelTouches")
    relative_size: float = Field(alias="RelativeSize")
