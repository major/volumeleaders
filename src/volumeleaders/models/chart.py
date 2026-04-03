"""Chart and market data response models."""

from pydantic import Field

from volumeleaders.models.base import AspNetDate, VLBaseModel


class PriceBar(VLBaseModel):
    """One-minute OHLCV bar with trade metadata overlays."""

    date_key: int = Field(alias="DateKey")
    time_key: int = Field(alias="TimeKey")
    security_key: int = Field(alias="SecurityKey")
    trade_id: int = Field(alias="TradeID")
    date: AspNetDate = Field(alias="Date")
    date_string: str | None = Field(alias="DateString")
    full_date_time: str = Field(alias="FullDateTime")
    min_full_date_time: str | None = Field(alias="MinFullDateTime")
    max_full_date_time: str | None = Field(alias="MaxFullDateTime")
    full_date_time_plotted: str | None = Field(alias="FullDateTimePlotted")
    full_time_string24: str = Field(alias="FullTimeString24")
    ticker: str | None = Field(alias="Ticker")
    volume: int = Field(alias="Volume")
    dollars: float = Field(alias="Dollars")
    open_price: float = Field(alias="OpenPrice")
    close_price: float = Field(alias="ClosePrice")
    high_price: float = Field(alias="HighPrice")
    low_price: float = Field(alias="LowPrice")
    price: float | None = Field(alias="Price")
    trades: int = Field(alias="Trades")
    block_size_ntile: float | None = Field(alias="BlockSizeNTile")
    cumulative_distribution: float = Field(alias="CumulativeDistribution")
    trade_conditions: str | None = Field(alias="TradeConditions")
    dark_pool_trade: bool = Field(alias="DarkPoolTrade")
    late_print: bool = Field(alias="LatePrint")
    opening_trade: bool = Field(alias="OpeningTrade")
    closing_trade: bool = Field(alias="ClosingTrade")
    signature_print: bool = Field(alias="SignaturePrint")
    phantom_print: bool = Field(alias="PhantomPrint")
    sweep: bool = Field(alias="Sweep")
    dates: str | None = Field(alias="Dates")
    trade_rank: int = Field(alias="TradeRank")
    trade_rank_snapshot: int = Field(alias="TradeRankSnapshot")
    trade_level_rank: int = Field(alias="TradeLevelRank")
    last_comparible_trade_date: AspNetDate = Field(alias="LastComparibleTradeDate")
    ipo_date: AspNetDate = Field(alias="IPODate")
    dollars_multiplier: float = Field(alias="DollarsMultiplier")
    shares_multiplier: float = Field(alias="SharesMultiplier")
    relative_size: float = Field(alias="RelativeSize")
    total_trades: int = Field(alias="TotalTrades")
    frequency_last_30_td: int = Field(alias="FrequencyLast30TD")
    frequency_last_90_td: int = Field(alias="FrequencyLast90TD")
    frequency_last_1_cy: int = Field(alias="FrequencyLast1CY")


class Company(VLBaseModel):
    """Reference metadata for a company or ETF."""

    security_key: int = Field(alias="SecurityKey")
    security_type_key: int = Field(alias="SecurityTypeKey")
    active: bool = Field(alias="Active")
    valid: bool = Field(alias="Valid")
    name: str = Field(alias="Name")
    ticker: str = Field(alias="Ticker")
    sector: str | None = Field(alias="Sector")
    industry: str | None = Field(alias="Industry")
    description: str | None = Field(alias="Description")
    home_page_url: str | None = Field(alias="HomePageURL")
    ipo_date: AspNetDate = Field(alias="IPODate")
    average_block_size_dollars: float = Field(alias="AverageBlockSizeDollars")
    average_block_size_dollars_30_days: float = Field(
        alias="AverageBlockSizeDollars30Days"
    )
    average_block_size_dollars_90_days: float = Field(
        alias="AverageBlockSizeDollars90Days"
    )
    average_block_size_shares: int = Field(alias="AverageBlockSizeShares")
    average_daily_volume: int = Field(alias="AverageDailyVolume")
    average_daily_volume_30_days: int = Field(alias="AverageDailyVolume30Days")
    average_daily_volume_90_days: int = Field(alias="AverageDailyVolume90Days")
    average_trade_shares: int = Field(alias="AverageTradeShares")
    average_trade_shares_30_days: int = Field(alias="AverageTradeShares30Days")
    average_trade_shares_90_days: int = Field(alias="AverageTradeShares90Days")
    average_daily_range: float = Field(alias="AverageDailyRange")
    average_daily_range_30_days: float = Field(alias="AverageDailyRange30Days")
    average_daily_range_90_days: float = Field(alias="AverageDailyRange90Days")
    average_daily_range_pct: float = Field(alias="AverageDailyRangePct")
    average_daily_range_pct_30_days: float = Field(alias="AverageDailyRangePct30Days")
    average_daily_range_pct_90_days: float = Field(alias="AverageDailyRangePct90Days")
    average_qualifying_block_trades: int = Field(alias="AverageQualifyingBlockTrades")
    average_closing_trade_shares: int = Field(alias="AverageClosingTradeShares")
    average_closing_trade_dollars: float = Field(alias="AverageClosingTradeDollars")
    average_closing_trade_dollars_30_days: float = Field(
        alias="AverageClosingTradeDollars30Days"
    )
    average_closing_trade_dollars_90_days: float = Field(
        alias="AverageClosingTradeDollars90Days"
    )
    average_cluster_size_dollars: float = Field(alias="AverageClusterSizeDollars")
    average_level_size_dollars: float = Field(alias="AverageLevelSizeDollars")
    priority: int = Field(alias="Priority")
    free: bool = Field(alias="Free")
    total_trades: int = Field(alias="TotalTrades")
    first_trade_date: AspNetDate = Field(alias="FirstTradeDate")
    previous_ticker: str | None = Field(alias="PreviousTicker")
    previous_ticker_expiration_date: AspNetDate = Field(
        alias="PreviousTickerExpirationDate"
    )
    news: str | None = Field(alias="News")
    financials: str | None = Field(alias="Financials")
    current_price: float | None = Field(alias="CurrentPrice")
    splits: str | None = Field(alias="Splits")
    market_cap: float = Field(alias="MarketCap")
    max_date: AspNetDate = Field(alias="MaxDate")
    options_enabled: bool = Field(alias="OptionsEnabled")


class Quote(VLBaseModel):
    """Bid/ask quote payload in snapshot responses."""

    timestamp: int = Field(alias="t")
    bid_price: float = Field(alias="p")
    bid_size: int = Field(alias="s")
    ask_price: float = Field(alias="P")
    ask_size: int = Field(alias="S")


class LastTrade(VLBaseModel):
    """Most recent trade payload in snapshot responses."""

    price: float = Field(alias="p")


class Snapshot(VLBaseModel):
    """Ticker snapshot combining quote and last-trade context."""

    last_quote: Quote = Field(alias="lastQuote")
    last_trade: LastTrade = Field(alias="lastTrade")
    ticker: str = Field(alias="ticker")
    todays_change: float = Field(alias="todaysChange")
    todays_change_perc: float = Field(alias="todaysChangePerc")


class SnapshotResponse(VLBaseModel):
    """Envelope returned by the GetSnapshot endpoint."""

    snapshot: Snapshot = Field(alias="ticker")
    status: str = Field(alias="status")
