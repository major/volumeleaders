"""Alert configuration and alert result models."""

from pydantic import Field

from volumeleaders.models.base import AspNetDate, VLBaseModel
from volumeleaders.models.trades import TradeCluster


class AlertConfig(VLBaseModel):
    """Saved alert configuration row."""

    alert_config_key: int = Field(alias="AlertConfigKey")
    user_key: int = Field(alias="UserKey")
    name: str = Field(alias="Name")
    tickers: str = Field(alias="Tickers")
    trade_rank_lte: int | None = Field(alias="TradeRankLTE")
    trade_vcd_gte: float | None = Field(alias="TradeVCDGTE")
    trade_mult_gte: float | None = Field(alias="TradeMultGTE")
    trade_volume_gte: int | None = Field(alias="TradeVolumeGTE")
    trade_dollars_gte: float | None = Field(alias="TradeDollarsGTE")
    trade_conditions: str | None = Field(alias="TradeConditions")
    trade_cluster_rank_lte: int | None = Field(alias="TradeClusterRankLTE")
    trade_cluster_vcd_gte: float | None = Field(alias="TradeClusterVCDGTE")
    trade_cluster_mult_gte: float | None = Field(alias="TradeClusterMultGTE")
    trade_cluster_volume_gte: int | None = Field(alias="TradeClusterVolumeGTE")
    trade_cluster_dollars_gte: float | None = Field(alias="TradeClusterDollarsGTE")
    total_rank_lte: int | None = Field(alias="TotalRankLTE")
    total_volume_gte: int | None = Field(alias="TotalVolumeGTE")
    total_dollars_gte: float | None = Field(alias="TotalDollarsGTE")
    ah_rank_lte: int | None = Field(alias="AHRankLTE")
    ah_volume_gte: int | None = Field(alias="AHVolumeGTE")
    ah_dollars_gte: float | None = Field(alias="AHDollarsGTE")
    closing_trade_rank_lte: int | None = Field(alias="ClosingTradeRankLTE")
    closing_trade_vcd_gte: float | None = Field(alias="ClosingTradeVCDGTE")
    closing_trade_mult_gte: float | None = Field(alias="ClosingTradeMultGTE")
    closing_trade_volume_gte: int | None = Field(alias="ClosingTradeVolumeGTE")
    closing_trade_dollars_gte: float | None = Field(alias="ClosingTradeDollarsGTE")
    closing_trade_conditions: str | None = Field(alias="ClosingTradeConditions")
    offsetting_print: bool = Field(alias="OffsettingPrint")
    phantom_print: bool = Field(alias="PhantomPrint")
    sweep: bool = Field(alias="Sweep")
    dark_pool: bool = Field(alias="DarkPool")


class TradeAlert(VLBaseModel):
    """Trade alert row containing trade details and alert metadata."""

    date: AspNetDate = Field(alias="Date")
    start_date: AspNetDate = Field(alias="StartDate")
    end_date: AspNetDate = Field(alias="EndDate")
    full_time_string24: str = Field(alias="FullTimeString24")
    date_key: int = Field(alias="DateKey")
    security_key: int = Field(alias="SecurityKey")
    time_key: int = Field(alias="TimeKey")
    trade_id: int = Field(alias="TradeID")
    sequence_number: int = Field(alias="SequenceNumber")
    user_key: int = Field(alias="UserKey")
    user_keys: str | None = Field(alias="UserKeys")
    sent: bool = Field(alias="Sent")
    email: str | None = Field(alias="Email")
    emails: str | None = Field(alias="Emails")
    ticker: str = Field(alias="Ticker")
    sector: str | None = Field(alias="Sector")
    industry: str | None = Field(alias="Industry")
    name: str = Field(alias="Name")
    alert_type: str = Field(alias="AlertType")
    price: float = Field(alias="Price")
    trade_rank: int = Field(alias="TradeRank")
    volume_cumulative_distribution: float = Field(alias="VolumeCumulativeDistribution")
    dollars_multiplier: float = Field(alias="DollarsMultiplier")
    volume: int = Field(alias="Volume")
    dollars: float = Field(alias="Dollars")
    last_comparible_trade_date_key: int = Field(alias="LastComparibleTradeDateKey")
    last_comparible_trade_date: AspNetDate = Field(alias="LastComparibleTradeDate")
    offsetting_trade_date: AspNetDate = Field(alias="OffsettingTradeDate")
    phantom_print_fulfillment_date: AspNetDate = Field(
        alias="PhantomPrintFulfillmentDate"
    )
    full_date_time: str = Field(alias="FullDateTime")
    ipo_date: AspNetDate = Field(alias="IPODate")
    rsi_hour: float = Field(alias="RSIHour")
    rsi_day: float = Field(alias="RSIDay")
    in_process: bool = Field(alias="InProcess")
    complete: bool = Field(alias="Complete")
    sweep: bool = Field(alias="Sweep")
    dark_pool: bool = Field(alias="DarkPool")
    late_print: bool = Field(alias="LatePrint")
    closing_trade: bool = Field(alias="ClosingTrade")
    signature_print: bool = Field(alias="SignaturePrint")
    phantom_print: bool = Field(alias="PhantomPrint")


class TradeClusterAlert(TradeCluster):
    """Trade cluster alert row."""
