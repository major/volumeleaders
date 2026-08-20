# endpoints/ - API Endpoint Functions

## OVERVIEW

Standalone functions that build requests, call `client.post_json()` or `client.post_datatables()`, and return typed model lists. One file per API domain.

## WHERE TO LOOK

| Task | File | Notes |
|------|------|-------|
| Add JSON endpoint | Follow `exhaustion.py` / `sector.py` | Simplest: build dict, call `post_json`, validate |
| Add Form-encoded endpoint | Follow `sector.py` (`get_sector_daily_returns`) | Build urlencoded body string, call `post_form`, validate |
| Add DataTables endpoint | Follow `earnings.py` | Define columns list, build `DataTablesRequest`, call `post_datatables` |
| Add filtered DataTables | Follow `trades.py` | Full filter set via `custom_filters` dict |
| Unique response parsing | `chart.py` | `get_price_data` unwraps nested arrays; `get_snapshot` uses envelope model |

## REQUEST PATTERNS

**Pattern 1: JSON body** (simple endpoints)
- Used by: `exhaustion.py`, `chart.py` (get_price_data, get_snapshot, get_company), `sector.py`, `darkpool.py`
- Flow: `dict -> client.post_json(path, payload) -> [Model.model_validate(row) for row in response]`
- No column specs needed

**Pattern 2: Form-encoded body** (direct form POST endpoints)
- Used by: `sector.py` (`get_sector_daily_returns`)
- Flow: `urlencode(dict) -> client.post_form(path, body) -> [Model.model_validate(row) for row in response]`

**Pattern 3: DataTables form-encoded** (table endpoints)
- Used by: `trades.py`, `levels.py`, `volume.py`, `earnings.py`, `watchlist.py`, `alerts.py`
- Flow: define `COLUMNS` list -> `DataTablesRequest(columns, custom_filters) -> client.post_datatables(path, request.encode()) -> [Model.model_validate(row) for row in rows]`
- Column specs are module-level `ALL_CAPS` lists

## CONVENTIONS

- **Function signature**: `def get_X(client: VolumeLeadersClient, *, <keyword-only params>) -> list[Model]`
- **Keyword-only args**: Everything after `client` is keyword-only (enforced by `*`)
- **Default filter values**: Match the VL web UI defaults (e.g., `min_dollars=500_000`, `relative_size=5`)
- **Column lists**: Module-level constants, one per endpoint function. Some columns appear twice (display + sort key).
- **Return types**: `list[Model]` for DataTables, single `Model` for JSON (except `get_all_snapshots` -> `dict[str, float]`)
- **Date params**: Accept `str` in `YYYY-MM-DD` format. `chart.py` has `_to_date_key()` helper for YYYYMMDD conversion.
- **No pagination logic**: Callers control `start`/`length` directly

## ANTI-PATTERNS

- Putting request logic in `_client.py` (keep it in endpoint files)
- Hardcoding filter values without defaults (always provide VL UI defaults)
- Returning raw dicts (always return typed Pydantic models)
- Sharing column lists between endpoints (each endpoint owns its column spec)

**Keep this file updated** when adding new endpoints, changing request patterns, or modifying function signatures.
