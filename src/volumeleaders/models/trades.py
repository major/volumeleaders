"""Trade and trade cluster response models."""

from pydantic import Field

from volumeleaders.models.base import AspNetDate, VLBaseModel


class Trade(VLBaseModel):
    """Single trade row returned by trade-related DataTables endpoints."""

    date: AspNetDate = Field(alias="Date")
    start_date: AspNetDate = Field(alias="StartDate")
    end_date: AspNetDate = Field(alias="EndDate")
    td30: AspNetDate = Field(alias="TD30")
    td90: AspNetDate = Field(alias="TD90")
    td1cy: AspNetDate = Field(alias="TD1CY")
    date_key: int = Field(alias="DateKey")
    time_key: int = Field(alias="TimeKey")
    security_key: int = Field(alias="SecurityKey")
    trade_id: int = Field(alias="TradeID")
    sequence_number: int = Field(alias="SequenceNumber")
    eom: bool = Field(alias="EOM")
    eoq: bool = Field(alias="EOQ")
    eoy: bool = Field(alias="EOY")
    opex: bool = Field(alias="OPEX")
    volex: bool = Field(alias="VOLEX")
    ticker: str = Field(alias="Ticker")
    sector: str = Field(alias="Sector")
    industry: str | None = Field(alias="Industry")
    name: str = Field(alias="Name")
    full_date_time: str | None = Field(alias="FullDateTime")
    full_time_string24: str | None = Field(alias="FullTimeString24")
    price: float = Field(alias="Price")
    bid: float = Field(alias="Bid")
    ask: float = Field(alias="Ask")
    dollars: float = Field(alias="Dollars")
    average_block_size_dollars: float = Field(alias="AverageBlockSizeDollars")
    average_block_size_shares: int = Field(alias="AverageBlockSizeShares")
    dollars_multiplier: float = Field(alias="DollarsMultiplier")
    volume: int = Field(alias="Volume")
    average_daily_volume: int = Field(alias="AverageDailyVolume")
    percent_daily_volume: float = Field(alias="PercentDailyVolume")
    last_comparible_trade_date: AspNetDate = Field(alias="LastComparibleTradeDate")
    ipo_date: AspNetDate = Field(alias="IPODate")
    offsetting_trade_date: AspNetDate = Field(alias="OffsettingTradeDate")
    phantom_print_fulfillment_date: AspNetDate = Field(
        alias="PhantomPrintFulfillmentDate"
    )
    phantom_print_fulfillment_days: int | None = Field(
        alias="PhantomPrintFulfillmentDays"
    )
    trade_count: int = Field(alias="TradeCount")
    cumulative_distribution: float = Field(alias="CumulativeDistribution")
    trade_rank: int = Field(alias="TradeRank")
    trade_rank_snapshot: int = Field(alias="TradeRankSnapshot")
    late_print: bool = Field(alias="LatePrint")
    sweep: bool = Field(alias="Sweep")
    dark_pool: bool = Field(alias="DarkPool")
    opening_trade: bool = Field(alias="OpeningTrade")
    closing_trade: bool = Field(alias="ClosingTrade")
    phantom_print: bool = Field(alias="PhantomPrint")
    inside_bar: bool = Field(alias="InsideBar")
    double_inside_bar: bool = Field(alias="DoubleInsideBar")
    signature_print: bool = Field(alias="SignaturePrint")
    new_position: bool = Field(alias="NewPosition")
    ah_institutional_dollars: float = Field(alias="AHInstitutionalDollars")
    ah_institutional_dollars_rank: int = Field(alias="AHInstitutionalDollarsRank")
    ah_institutional_volume: int = Field(alias="AHInstitutionalVolume")
    total_institutional_dollars: float = Field(alias="TotalInstitutionalDollars")
    total_institutional_dollars_rank: int = Field(alias="TotalInstitutionalDollarsRank")
    total_institutional_volume: int = Field(alias="TotalInstitutionalVolume")
    closing_trade_dollars: float = Field(alias="ClosingTradeDollars")
    closing_trade_dollars_rank: int = Field(alias="ClosingTradeDollarsRank")
    closing_trade_volume: int = Field(alias="ClosingTradeVolume")
    total_dollars: float = Field(alias="TotalDollars")
    total_dollars_rank: int = Field(alias="TotalDollarsRank")
    total_volume: int = Field(alias="TotalVolume")
    close_price: float = Field(alias="ClosePrice")
    rsi_hour: float = Field(alias="RSIHour")
    rsi_day: float = Field(alias="RSIDay")
    total_rows: int = Field(alias="TotalRows")
    trade_conditions: str | None = Field(alias="TradeConditions")
    frequency_last_30_td: int = Field(alias="FrequencyLast30TD")
    frequency_last_90_td: int = Field(alias="FrequencyLast90TD")
    frequency_last_1_cy: int = Field(alias="FrequencyLast1CY")
    cancelled: bool = Field(alias="Cancelled")
    total_trades: int = Field(alias="TotalTrades")
    external_feed: bool = Field(alias="ExternalFeed")


class _TradeClusterBase(VLBaseModel):
    """Shared fields for trade cluster and trade cluster bomb models."""

    date: AspNetDate = Field(alias="Date")
    date_key: int = Field(alias="DateKey")
    security_key: int = Field(alias="SecurityKey")
    ticker: str = Field(alias="Ticker")
    sector: str = Field(alias="Sector")
    industry: str | None = Field(alias="Industry")
    name: str = Field(alias="Name")
    min_full_date_time: str = Field(alias="MinFullDateTime")
    max_full_date_time: str = Field(alias="MaxFullDateTime")
    min_full_time_string24: str = Field(alias="MinFullTimeString24")
    max_full_time_string24: str = Field(alias="MaxFullTimeString24")
    close_price: float = Field(alias="ClosePrice")
    dollars: float = Field(alias="Dollars")
    average_block_size_shares: int = Field(alias="AverageBlockSizeShares")
    average_block_size_dollars: float = Field(alias="AverageBlockSizeDollars")
    volume: int = Field(alias="Volume")
    trade_count: int = Field(alias="TradeCount")
    ipo_date: AspNetDate = Field(alias="IPODate")
    dollars_multiplier: float = Field(alias="DollarsMultiplier")
    cumulative_distribution: float = Field(alias="CumulativeDistribution")
    average_daily_volume: int = Field(alias="AverageDailyVolume")
    eom: bool = Field(alias="EOM")
    eoq: bool = Field(alias="EOQ")
    eoy: bool = Field(alias="EOY")
    opex: bool = Field(alias="OPEX")
    volex: bool = Field(alias="VOLEX")
    inside_bar: bool = Field(alias="InsideBar")
    double_inside_bar: bool = Field(alias="DoubleInsideBar")
    total_rows: int = Field(alias="TotalRows")
    external_feed: bool = Field(alias="ExternalFeed")


class TradeCluster(_TradeClusterBase):
    """Aggregated trade cluster row returned by cluster endpoints."""

    price: float = Field(alias="Price")
    last_comparible_trade_cluster_date: AspNetDate = Field(
        alias="LastComparibleTradeClusterDate"
    )
    trade_cluster_rank: int = Field(alias="TradeClusterRank")


class TradeClusterBomb(_TradeClusterBase):
    """Trade cluster bomb row, cluster metrics with bomb-specific ranking."""

    last_comparable_trade_cluster_bomb_date: AspNetDate = Field(
        alias="LastComparableTradeClusterBombDate"
    )
    trade_cluster_bomb_rank: int = Field(alias="TradeClusterBombRank")
