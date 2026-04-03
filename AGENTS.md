# PROJECT KNOWLEDGE BASE

**Generated:** 2026-04-02
**Branch:** main (pre-initial-commit)

## OVERVIEW

Python API client library for [volumeleaders.com](https://www.volumeleaders.com), scraping institutional block trade data via browser cookie auth and ASP.NET endpoints. Mirrors the [tickerscope](~/git/major/tickerscope) client architecture.

## STRUCTURE

```text
src/volumeleaders/
    __init__.py              # Public API surface (45 exports)
    _client.py               # Thin httpx wrapper: auth state + two POST methods
    _auth.py                 # browser-cookie3 extraction, XSRF token from HTML
    _exceptions.py           # VolumeLeadersError -> CookieExtractionError, AuthenticationError, APIError
    _parsing.py              # /Date(ms)/ parser, snapshot string parser, datekey helpers
    _datatables.py           # DataTablesRequest dataclass -> URL-encoded form body
    models/                  # Pydantic v2 response models (see models/AGENTS.md)
    endpoints/               # Endpoint functions by domain (see endpoints/AGENTS.md)
    mcp/
        __init__.py          # FastMCP server instance + lifespan
        utils.py             # Shared helpers (client access, error handling, exhaustion)
        tools/
            __init__.py      # Imports all tool modules to trigger registration
            trade_level_touches.py  # trade_level_touches tool

tests/                       # Mirrors src/ layout, real API payloads as fixtures
    conftest.py              # 11 fixtures loading JSON from tests/fixtures/
    fixtures/                # Real API JSON response payloads for test validation
    test_models/             # Model.model_validate(real_row) tests
    test_endpoints/          # Mock client, verify typed returns
```

## WHERE TO LOOK

| Task | Location | Notes |
|------|----------|-------|
| Add new endpoint | `endpoints/<domain>.py` + `models/<domain>.py` | Follow existing pairs, add to both `__init__.py` re-exports |
| Add new model | `models/<domain>.py` | Inherit `VLBaseModel`, use `Field(alias="APIName")` |
| Fix auth issues | `_auth.py` | Cookie names: `__RequestVerificationToken`, `ASP.NET_SessionId`, `.ASPXAUTH` |
| Parse new date format | `_parsing.py` | ASP.NET sentinels: -62135596800000 (0001-01-01), -2208988800000 (1900-01-01) |
| Add test fixtures | `tests/conftest.py` + `tests/fixtures/` | Capture real JSON, add `@pytest.fixture` loader |
| Change CI pipeline | `Makefile` + `.github/workflows/ci.yml` | `ci` target: lint -> typecheck -> radon -> test |
| Add MCP tool | `src/volumeleaders/mcp/tools/<name>.py` | One file per tool, shared helpers in `mcp/utils.py` |

## CONVENTIONS

- **Private modules**: Underscore prefix (`_client.py`, `_auth.py`) = internal; public API only through `__init__.py`
- **Two request patterns**: JSON body (`post_json`) for simple endpoints, DataTables form-encoded (`post_datatables`) for table endpoints
- **Column specs**: Module-level `ALL_CAPS` lists in each endpoint file define DataTables column ordering
- **Model aliases**: Every field uses `Field(alias="PascalCaseAPIName")` with `populate_by_name=True`
- **Test imports**: Use `importlib.import_module()` not direct imports (avoids sys.path issues with src-layout)
- **Test data**: Real API payloads in `tests/fixtures/`, never synthetic/minimal JSON
- **Complexity cap**: Radon enforces A/B rating. Functions at C or higher fail CI.
- **Type checker**: `ty` (Red Hat's type checker, not pyright despite pyrightconfig.json existing)

## ANTI-PATTERNS

- `as any` / `@ts-ignore` equivalent: never suppress type errors
- Empty catch blocks: always handle or re-raise
- Synthetic test data: always validate models against real API payloads
- Fat client: `_client.py` stays thin (auth state + request helpers only); business logic lives in `endpoints/`
- Monolithic models: each endpoint gets purpose-built fields, not the full ~70-field API object

## UNIQUE STYLES

- **ASP.NET date type**: `AspNetDate = Annotated[datetime | None, BeforeValidator(_coerce_aspnet_date)]` used as field type annotation across all models
- **Sentinel values**: TradeRank 9999 = unranked. Two epoch values = null date. Handle in `_parsing.py`, never in models.
- **Client bypass in tests**: `object.__new__(VolumeLeadersClient)` to skip auth-heavy `__init__` during unit tests
- **Snapshot string**: `GetAllSnapshots` returns `"TICKER:PRICE;TICKER:PRICE;..."` not JSON, parsed by `parse_snapshot_string()`
- **Volume models**: `InstitutionalVolume` and `TotalVolume` inherit directly from `Trade` (same field set)

## COMMANDS

```bash
make lint          # ruff check src/ tests/
make format        # ruff format src/ tests/
make typecheck     # ty check src/
make radon         # fail if any function >= C complexity
make test          # pytest --cov
make ci            # lint + typecheck + radon + test
make docs          # properdocs build (requires docs dep group)
```

## NOTES

- CI runs on GitHub Actions (`.github/workflows/ci.yml`): lint, typecheck, radon, test. Mirrors `make ci`.
- Requires Python >= 3.14 (current stable).
- Auth requires user to be logged into volumeleaders.com in Firefox first. No programmatic login.
- MCP server: `uv run volumeleaders-mcp` or `uv run fastmcp dev src/volumeleaders/mcp/__init__.py`.
- **Keep AGENTS.md current**: Update this file and its children (`src/volumeleaders/AGENTS.md`, `models/AGENTS.md`, `endpoints/AGENTS.md`) when adding modules, changing conventions, or altering the project structure.
- **Keep README.md current**: Update README.md when adding new endpoints, changing usage patterns, or altering the public API surface. README.md is user-facing documentation and should reflect the current state of the library.
