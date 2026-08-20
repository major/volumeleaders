"""Sector breakdown, theme notional, supply/demand, and performance models."""

from __future__ import annotations

from pydantic import Field

from volumeleaders.models.base import AspNetDate, VLBaseModel


class SectorBreakdown(VLBaseModel):
    """Daily institutional dollar volume breakdown for a sector."""

    date_key: int = Field(alias="DateKey")
    sector: str = Field(alias="Sector")
    dollars: float = Field(alias="Dollars")


class InstitutionalOutlier(VLBaseModel):
    """Statistical outlier trade volume record (Z-score sigmas above baseline)."""

    date: AspNetDate = Field(alias="Date")
    ticker: str = Field(alias="Ticker")
    sector: str = Field(alias="Sector")
    industry: str = Field(alias="Industry")
    trade_rank: int = Field(alias="TradeRank")
    volume: int = Field(alias="Volume")
    price: float = Field(alias="Price")
    dollars: float = Field(alias="Dollars")
    avg_dollars: float = Field(alias="AvgDollars")
    std_dollars: float = Field(alias="STDDollars")
    sigmas: float = Field(alias="Sigmas")
    trade_count: int = Field(alias="TradeCount")


class SectorThemeNotional(VLBaseModel):
    """Hierarchical sector, theme, and ticker institutional notional allocation."""

    date_key: int = Field(alias="DateKey")
    sector: str = Field(alias="Sector")
    sector_rank: int = Field(alias="SectorRank")
    theme_key: int = Field(alias="ThemeKey")
    theme_slug: str = Field(alias="ThemeSlug")
    theme: str = Field(alias="Theme")
    theme_rank: int = Field(alias="ThemeRank")
    theme_pct_of_sector: float = Field(alias="ThemePctOfSector")
    ticker: str = Field(alias="Ticker")
    ticker_pct_of_theme: float = Field(alias="TickerPctOfTheme")
    volume: int = Field(alias="Volume")
    dollars: float = Field(alias="Dollars")
    trades: int = Field(alias="Trades")


class SupplyDemandArea(VLBaseModel):
    """Automated sector supply and demand level distribution statistics."""

    date_key: int = Field(alias="DateKey")
    sector: str = Field(alias="Sector")
    ticker_count: int = Field(alias="TickerCount")
    min_pct_levels_below_latest_close: float = Field(
        alias="MinPCTLevelsBelowLatestClose",
    )
    first_quartile_pct_levels_below_latest_close: float = Field(
        alias="FirstQuartilePCTLevelsBelowLatestClose",
    )
    median_pct_levels_below_latest_close: float = Field(
        alias="MedianPCTLevelsBelowLatestClose",
    )
    avg_pct_levels_below_latest_close: float = Field(
        alias="AvgPCTLevelsBelowLatestClose",
    )
    third_quartile_pct_levels_below_latest_close: float = Field(
        alias="ThirdQuartilePCTLevelsBelowLatestClose",
    )
    max_pct_levels_below_latest_close: float = Field(
        alias="MaxPCTLevelsBelowLatestClose",
    )


class SectorDailyReturn(VLBaseModel):
    """Daily sector performance, multi-factor, and benchmark metrics."""

    sector: str = Field(alias="Sector")
    date: AspNetDate = Field(alias="Date")
    date_key: int = Field(alias="DateKey")
    ticker_count: int = Field(alias="TickerCount")
    beta_10: float = Field(alias="Beta10")
    beta_20: float = Field(alias="Beta20")
    beta_40: float = Field(alias="Beta40")
    beta_blended: float = Field(alias="BetaBlended")
    momentum_10: float = Field(alias="Momentum10")
    momentum_20: float = Field(alias="Momentum20")
    momentum_40: float = Field(alias="Momentum40")
    momentum_blended: float = Field(alias="MomentumBlended")
    realized_vol_10: float = Field(alias="RealizedVol10")
    realized_vol_20: float = Field(alias="RealizedVol20")
    realized_vol_40: float = Field(alias="RealizedVol40")
    realized_vol_blended: float = Field(alias="RealizedVolBlended")
    relative_strength_10: float = Field(alias="RelativeStrength10")
    relative_strength_20: float = Field(alias="RelativeStrength20")
    relative_strength_40: float = Field(alias="RelativeStrength40")
    relative_strength_blended: float = Field(alias="RelativeStrengthBlended")
    sharpe_10: float = Field(alias="Sharpe10")
    sharpe_20: float = Field(alias="Sharpe20")
    sharpe_40: float = Field(alias="Sharpe40")
    sharpe_blended: float = Field(alias="SharpeBlended")
    sector_daily_return: float = Field(alias="SectorDailyReturn")
    sector_daily_return_pct: float = Field(alias="SectorDailyReturnPct")
    pct_tickers_positive: float = Field(alias="PctTickersPositive")
    spy_close: float = Field(alias="SPYClose")
