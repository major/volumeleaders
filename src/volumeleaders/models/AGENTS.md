# models/ - Pydantic v2 Response Models

## OVERVIEW

One model file per endpoint domain. Every model inherits `VLBaseModel` and maps API PascalCase fields to snake_case via `Field(alias=...)`.

## STRUCTURE

```text
base.py          # VLBaseModel + AspNetDate annotated type
trades.py        # Trade (89 fields), TradeCluster, TradeClusterBomb
chart.py         # PriceBar, Company, Quote, LastTrade, Snapshot, SnapshotResponse
levels.py        # TradeLevel, TradeLevelTouch
volume.py        # InstitutionalVolume(Trade), TotalVolume(Trade) - empty subclasses
earnings.py      # Earnings (9 fields, simplest model)
exhaustion.py    # ExhaustionScore (5 fields)
watchlist.py     # WatchListTicker, WatchListConfig (86 lines, most filter fields)
alerts.py        # AlertConfig, TradeAlert, TradeClusterAlert(TradeCluster)
```

## WHERE TO LOOK

| Task | File | Notes |
|------|------|-------|
| Add new model | New `<domain>.py` | Inherit `VLBaseModel`, add to `__init__.py` |
| Add date field | Use `AspNetDate` type | Handles `/Date(ms)/` strings + null sentinels automatically |
| Extend existing model | Relevant `<domain>.py` | Keep `Field(alias="ExactAPIName")` |
| Reuse Trade fields | Subclass `Trade` directly | See `volume.py` for pattern |

## CONVENTIONS

- **Every field** has `Field(alias="PascalCaseAPIName")` matching the raw JSON key
- **Optional fields**: Use `str | None`, `float | None` etc. (never `Optional[X]`)
- **Date fields**: Always type as `AspNetDate`, never raw `str` or `datetime`
- **Boolean indicators**: EOM, EOQ, EOY, OPEX, VOLEX stored as individual `bool` fields
- **Inheritance**: Volume models subclass Trade (identical field set). TradeClusterAlert subclasses TradeCluster.
- **No default values** on model fields (API always provides them)
- **No validators** on individual fields (coercion happens in `AspNetDate` only)
- **Nested models**: Only in chart.py (Snapshot contains Quote + LastTrade; SnapshotResponse wraps Snapshot)

## ANTI-PATTERNS

- Adding fields not present in the API response (breaks `model_validate`)
- Using `datetime` directly instead of `AspNetDate` for API date fields
- Creating a "universal" model with all ~70 API fields
- Adding computed properties (keep models as pure data containers)

**Keep this file updated** when adding new models, changing field conventions, or introducing new base classes.
