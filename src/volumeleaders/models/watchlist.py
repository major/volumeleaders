"""Watch list endpoint response models."""

from pydantic import Field

from volumeleaders.models.base import AspNetDate, VLBaseModel


class WatchListTicker(VLBaseModel):
    """Ticker row returned for a selected watch list."""

    ticker: str = Field(alias="Ticker")
    price: float = Field(alias="Price")
    nearest_top10_trade_date: AspNetDate = Field(alias="NearestTop10TradeDate")
    nearest_top10_trade_cluster_date: AspNetDate = Field(
        alias="NearestTop10TradeClusterDate"
    )
    nearest_top10_trade_level: float | None = Field(alias="NearestTop10TradeLevel")


class WatchListConfig(VLBaseModel):
    """Saved watch list search template and filters."""

    search_template_key: int = Field(alias="SearchTemplateKey")
    user_key: int = Field(alias="UserKey")
    search_template_type_key: int = Field(alias="SearchTemplateTypeKey")
    name: str = Field(alias="Name")
    tickers: str = Field(alias="Tickers")
    sort_order: int | None = Field(alias="SortOrder")
    min_volume: int = Field(alias="MinVolume")
    max_volume: int = Field(alias="MaxVolume")
    min_dollars: float = Field(alias="MinDollars")
    max_dollars: float = Field(alias="MaxDollars")
    min_price: float = Field(alias="MinPrice")
    max_price: float = Field(alias="MaxPrice")
    rsi_overbought_hourly: int | None = Field(alias="RSIOverboughtHourly")
    rsi_overbought_daily: int | None = Field(alias="RSIOverboughtDaily")
    rsi_oversold_hourly: int | None = Field(alias="RSIOversoldHourly")
    rsi_oversold_daily: int | None = Field(alias="RSIOversoldDaily")
    conditions: str = Field(alias="Conditions")
    rsi_overbought_hourly_selected: bool | None = Field(
        alias="RSIOverboughtHourlySelected"
    )
    rsi_overbought_daily_selected: bool | None = Field(
        alias="RSIOverboughtDailySelected"
    )
    rsi_oversold_hourly_selected: bool | None = Field(alias="RSIOversoldHourlySelected")
    rsi_oversold_daily_selected: bool | None = Field(alias="RSIOversoldDailySelected")
    min_relative_size: int = Field(alias="MinRelativeSize")
    min_relative_size_selected: bool | None = Field(alias="MinRelativeSizeSelected")
    max_trade_rank: int = Field(alias="MaxTradeRank")
    security_type_key: int = Field(alias="SecurityTypeKey")
    security_type: str | None = Field(alias="SecurityType")
    max_trade_rank_selected: bool | None = Field(alias="MaxTradeRankSelected")
    min_vcd: int = Field(alias="MinVCD")
    normal_prints: bool = Field(alias="NormalPrints")
    signature_prints: bool = Field(alias="SignaturePrints")
    late_prints: bool = Field(alias="LatePrints")
    timely_prints: bool = Field(alias="TimelyPrints")
    dark_pools: bool = Field(alias="DarkPools")
    lit_exchanges: bool = Field(alias="LitExchanges")
    sweeps: bool = Field(alias="Sweeps")
    blocks: bool = Field(alias="Blocks")
    premarket_trades: bool = Field(alias="PremarketTrades")
    rth_trades: bool = Field(alias="RTHTrades")
    ah_trades: bool = Field(alias="AHTrades")
    opening_trades: bool = Field(alias="OpeningTrades")
    closing_trades: bool = Field(alias="ClosingTrades")
    phantom_trades: bool = Field(alias="PhantomTrades")
    offsetting_trades: bool = Field(alias="OffsettingTrades")
    normal_prints_selected: bool = Field(alias="NormalPrintsSelected")
    signature_prints_selected: bool = Field(alias="SignaturePrintsSelected")
    late_prints_selected: bool = Field(alias="LatePrintsSelected")
    timely_prints_selected: bool = Field(alias="TimelyPrintsSelected")
    dark_pools_selected: bool = Field(alias="DarkPoolsSelected")
    lit_exchanges_selected: bool = Field(alias="LitExchangesSelected")
    sweeps_selected: bool = Field(alias="SweepsSelected")
    blocks_selected: bool = Field(alias="BlocksSelected")
    premarket_trades_selected: bool = Field(alias="PremarketTradesSelected")
    rth_trades_selected: bool = Field(alias="RTHTradesSelected")
    ah_trades_selected: bool = Field(alias="AHTradesSelected")
    opening_trades_selected: bool = Field(alias="OpeningTradesSelected")
    closing_trades_selected: bool = Field(alias="ClosingTradesSelected")
    phantom_trades_selected: bool = Field(alias="PhantomTradesSelected")
    offsetting_trades_selected: bool = Field(alias="OffsettingTradesSelected")
    sector_industry: str | None = Field(alias="SectorIndustry")
    api_key: str | None = Field(alias="APIKey")
