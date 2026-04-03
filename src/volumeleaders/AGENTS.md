# src/volumeleaders/ - Package Internals

## OVERVIEW

Core package with 6 private modules and 3 subpackages. Public API exposed only through `__init__.py` (45 exports).

## MODULE ROLES

| Module | Purpose | Key Symbols |
|--------|---------|-------------|
| `__init__.py` | Public surface: re-exports everything | `__all__` (45 items), `main()` stub |
| `_client.py` | Thin httpx wrapper | `VolumeLeadersClient` (3 methods: `post_json`, `post_datatables`, `post_datatables_raw`) |
| `_auth.py` | Browser cookie extraction + XSRF | `extract_cookies()`, `fetch_xsrf_token()`, `BASE_URL`, `USER_AGENT` |
| `_exceptions.py` | Exception hierarchy | `VolumeLeadersError` -> `CookieExtractionError`, `AuthenticationError`, `APIError` |
| `_parsing.py` | Response format handlers | `parse_aspnet_date()`, `parse_snapshot_string()`, `parse_datekey()`, `format_datekey()`, `format_date()` |
| `_datatables.py` | Form body builder | `DataTablesRequest` dataclass with `encode()` -> URL-encoded string |
| `mcp/` | MCP server package | `mcp` (FastMCP instance), `main()`, tool functions |

## AUTH FLOW

```text
Firefox cookies (browser-cookie3) -> extract_cookies() -> 3 cookies
GET /ExecutiveSummary -> parse hidden input -> XSRF token
All API calls: cookies + x-xsrf-token + x-requested-with: XMLHttpRequest
```

Required cookies: `__RequestVerificationToken`, `ASP.NET_SessionId`, `.ASPXAUTH`

## CONVENTIONS

- **Underscore prefix** = private module (not importable by consumers)
- **Client stays thin**: only auth state + request helpers. No endpoint logic.
- **`post_datatables`** extracts `response["data"]` automatically. Use `post_datatables_raw` for full response with `recordsTotal`/`recordsFiltered`.
- **Exception context**: `CookieExtractionError` carries `browser` attr. `APIError` carries `status_code` attr.
- **`_XSRF_RE`** regex in `_auth.py` parses the hidden input. If VL changes their HTML structure, this breaks first.
- **Keep this file updated** when adding, removing, or renaming modules in this package.
