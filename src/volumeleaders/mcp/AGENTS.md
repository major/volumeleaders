# mcp/ - FastMCP Server Package

## OVERVIEW

MCP server modules that expose VolumeLeaders API data as LLM-callable tools using FastMCP.

## STRUCTURE

```text
mcp/
    __init__.py              # FastMCP server instance + lifespan
    utils.py                 # Shared helpers for all tools (client access, error handling, dates, dollars)
    tools/
        __init__.py          # Imports all tool modules to trigger registration
        trade_cluster_bombs.py  # trade_cluster_bombs tool
        trade_clusters.py    # trade_clusters tool
        trade_level_touches.py  # trade_level_touches tool
        trade_levels.py      # trade_levels tool
        trades.py            # trades tool (institutional block trades)
```

## MODULE ROLES

| Module | Purpose | Key Symbols |
|--------|---------|-------------|
| `__init__.py` | Server setup and lifecycle management | `VLContext`, `_lifespan()`, `mcp`, `main()` |
| `utils.py` | Shared utilities across tools | `resolve_client()`, `fetch_exhaustion_data()`, `capture_non_auth_error()`, `today_date_string()`, `one_week_ago_date_string()`, `ninety_days_ago_date_string()`, `count_rows()`, `format_date()`, `format_dollars()`, `curate_exhaustion()` |
| `tools/__init__.py` | Tool registration imports | Imports all tool modules as side effect |
| `tools/trade_cluster_bombs.py` | Trade cluster bomb scanner | `trade_cluster_bombs()` and private `_curate_bomb()` |
| `tools/trade_clusters.py` | Trade cluster scanner | `trade_clusters()` and private `_curate_cluster()` |
| `tools/trade_level_touches.py` | Trade level touch scanner | `trade_level_touches()` and private curation/filter helpers |
| `tools/trade_levels.py` | Trade level lookup for a ticker | `trade_levels()` and private `_curate_level()` |
| `tools/trades.py` | Institutional block trade scanner | `trades()` and private `_curate_trade()`, `_resolve_dates()`, `_resolve_include_flags()`, `_format_time()`, `_collect_trade_types()` |

## CLIENT LIFECYCLE

- `VolumeLeadersClient` is initialized once in MCP lifespan startup.
- The shared client is stored in `VLContext` and reused across tool calls.
- Lifespan shutdown always calls `client.close()`.
- Tools access the client via `resolve_client(ctx)` from `utils.py`.

## RESPONSE CONTRACT

Tools return a dict envelope with stable keys:

- `query` (optional): normalized/resolved inputs, included when `include_query=True`. Useful for debugging resolved filter defaults.
- `data`: curated endpoint data (tool-specific structure)
- `summary` (optional): concise natural-language summary for LLM consumption. Included when it adds value beyond metadata.
- `warnings` (conditional): non-fatal endpoint errors. Omitted when empty to save tokens.
- `metadata`: response metadata such as truncation and selected limits

## TOOLS

- `trade_clusters`: Scanner for institutional trade clusters on a given day. A trade cluster is a group of institutional block trades in the same security occurring within a time window. date defaults to today (used as both start and end date). Returns compact cluster rows (ticker, time_range, trade_count, price, dollars formatted, volume, rank, dollars_multiplier, cumulative_distribution, last_comparable_date). Supports tickers, date, max_results, and include_query parameters.

- `trade_cluster_bombs`: Scanner for trade cluster bomb events over a date range. A cluster bomb is an exceptionally large trade cluster representing extraordinary institutional conviction. start_date defaults to one week ago, end_date defaults to today (bombs are rare, wider window captures recent events). Returns compact bomb rows (ticker, time_range, trade_count, sector, industry, dollars formatted, volume, rank, dollars_multiplier, cumulative_distribution, last_comparable_date). Supports tickers, start_date, end_date, max_results, and include_query parameters.

- `trade_level_touches`: Token-optimized scanner for trade level touch events. A trade level is a price where institutional block trades have accumulated; a touch is when price revisits that level intraday. Context-aware filter defaults: ticker queries get permissive filters (RelativeSize=0, TradeLevelRank=10, MinDollars=$500K), broad scans use tighter filters (RelativeSize=5, TradeLevelRank=5, MinDollars=$500M). Returns compact touch rows (ticker, time, price, dollars as formatted string like "$11.4B", volume, trades, rank, relative_size, level_origin_date, level_last_confirmed). No ticker metadata, no summary. Query block opt-in via `include_query`. Warnings omitted when empty. Supports date, tickers, relative_size, trade_level_rank, min_dollars, max_results, and include_query parameters.

- `trade_levels`: Lookup of institutional trade levels for a single ticker. Requires a ticker symbol. end_date defaults to today, start_date defaults to one year ago (lookback window for computing levels from historical block trades). Returns compact level rows (price, dollars formatted like "$166.5M", volume, trades, rank, relative_size, cumulative_distribution, level_origin_date, level_last_confirmed). No ticker in output (single-ticker tool, redundant). trade_level_rank defaults to -1 (no filter, matching VL web UI behavior). Supports ticker (required), start_date, end_date, min_dollars, relative_size, trade_level_rank, trade_level_count, and include_query parameters.

- `trades`: Institutional block trade scanner with context-aware defaults. A block trade is a large-volume transaction by institutional investors. Context-aware date and filter defaults: ticker queries get 90-day lookback with phantom/offsetting included, broad scans default to today only with phantom/offsetting excluded. trade_rank defaults to 100 (ranked trades only). Returns compact trade rows (ticker, date, time, price, current_price from snapshots, dollars formatted, volume, trade_rank, dollars_multiplier, cumulative_distribution, trade_count, types as list like ["dark_pool", "sweep"] or ["block"] for standard trades, sector, last_comparable_date). Sortable by time (default, newest first), rank (best first), dollars (biggest first), or multiplier (most unusual first). Supports pagination via offset + max_results. Supports tickers, start_date, end_date, trade_rank, min_dollars, min_volume, sort_by, offset, and max_results parameters.

## CONVENTIONS

- Register tools with `@mcp.tool` from `volumeleaders.mcp`.
- Each tool lives in its own file under `tools/`.
- Shared helpers go in `utils.py`, tool-specific helpers stay private in the tool file.
- Keep tool return values as plain dict/list primitives (not full Pydantic model dumps).
- Curate high-signal fields from large endpoint models.
- Include a `summary` string when it adds value beyond metadata. Omit for token-optimized tools.
- Include `warnings` only when non-empty. Omit the key entirely for clean responses.

## ADDING A NEW TOOL

1. Create a new file in `tools/` (e.g., `tools/my_tool.py`).
2. Import `mcp` from `volumeleaders.mcp` and decorate the tool function with `@mcp.tool`.
3. Access the client via `resolve_client(ctx)` from `utils.py`.
4. Return the standard envelope shape (`query`/`data`/`warnings`/`metadata`, optionally `summary`).
5. Add the import to `tools/__init__.py`.
6. Add unit tests in `tests/test_mcp/`.
7. Update this file and parent AGENTS docs if conventions or module roles change.
