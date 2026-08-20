# Python client and MCP server for volumeleaders.com

> **Unofficial.** This project is not affiliated with, endorsed by, or connected to [volumeleaders.com](https://www.volumeleaders.com) in any way.

Python client and [MCP server](https://modelcontextprotocol.io/) for [volumeleaders.com](https://www.volumeleaders.com) institutional block trade data.

Use it as a **Python library** to query institutional block trades, trade clusters, trade levels, and more with typed Pydantic models. Or run it as an **MCP server** to give AI coding assistants direct access to the same data.

Authentication works by extracting cookies from your browser session (no API keys needed).

## Prerequisites

You must be logged into volumeleaders.com in Firefox before using the client. The library reads your browser cookies for authentication (there is no programmatic login).

## Install

```bash
pip install volumeleaders
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
uv add volumeleaders
```

## Usage

```python
from volumeleaders import VolumeLeadersClient, get_trades, get_exhaustion_scores

with VolumeLeadersClient() as client:
    # Fetch institutional trades for a date range
    trades = get_trades(
        client,
        start_date="2026-03-01",
        end_date="2026-03-31",
        tickers="AAPL",
    )
    for trade in trades:
        print(f"{trade.ticker} {trade.trade} @ {trade.current}")

    # Get exhaustion scores for today
    scores = get_exhaustion_scores(client)
    print(scores)
```

### Available endpoints

| Function | Description |
|----------|-------------|
| `get_trades` | Institutional block trades with full filter set |
| `get_trade_clusters` | Clustered trade activity |
| `get_trade_cluster_bombs` | Large cluster events |
| `get_exhaustion_scores` | Daily exhaustion score ranks |
| `get_earnings` | Earnings data |
| `get_company` | Company metadata |
| `get_snapshot` | Chart snapshot for a ticker |
| `get_all_snapshots` | Price snapshots for all tickers |
| `get_price_data` | Price/volume bar data |
| `get_chart_levels` | Chart trade levels |
| `get_trade_levels` | Trade level data |
| `get_trade_level_touches` | Trade level touch events |
| `get_institutional_volume` | Institutional volume |
| `get_ah_institutional_volume` | After-hours institutional volume |
| `get_total_volume` | Total volume |
| `get_trade_alerts` | Trade alerts |
| `get_trade_cluster_alerts` | Trade cluster alerts |
| `get_alert_configs` | Alert configurations |
| `get_watchlist_configs` | Watchlist configurations |
| `get_watchlist_tickers` | Tickers in a watchlist |
| `get_sector_breakdown` | Daily institutional dollar volume by sector |
| `get_institutional_outliers` | Statistical block trade volume outliers |
| `get_notional_by_sector_by_name` | Hierarchical sector, theme, and ticker capital flows |
| `get_supply_demand_areas` | Automated sector supply and demand support scores |
| `get_sector_daily_returns` | Multi-factor sector metrics, momentum, Sharpe, and risk |
| `get_dark_pool_volume_report` | Binned dark pool volume distribution profiles |

All endpoint functions take a `VolumeLeadersClient` as the first argument and return typed Pydantic models.

## MCP Server

The library includes an [MCP](https://modelcontextprotocol.io/) server that exposes VolumeLeaders data as tools for AI coding assistants. 12 tools are available:

- `trades`: Institutional block trade scanner with context-aware defaults.
- `trade_clusters`: Institutional trade cluster scanner for a given day.
- `trade_cluster_bombs`: Large trade cluster bomb events over date ranges.
- `trade_levels`: Institutional trade levels for a ticker symbol.
- `trade_level_touches`: Intraday trade level touch scanner.
- `sector_flows`: Daily institutional dollar flows and market share across sectors.
- `institutional_outliers`: Statistical block trade volume anomalies (Z-scores).
- `sector_themes`: Hierarchical capital allocation (Sector -> Theme -> Tickers).
- `sector_support_scores`: Automated supply and demand support score distributions.
- `sector_factors`: Multi-factor sector scorecard (Momentum, Sharpe, Beta, Volatility).
- `sector_rotation_rrg`: JdK Relative Rotation Graph (RRG) modeling against SPY.
- `dark_pool_profile`: Dark pool price-volume profile and Point-of-Control (POC).

### Quick start with uv

No installation needed:

```bash
uv run --with "volumeleaders[mcp]" volumeleaders-mcp
```

Or if the package is already installed:

```bash
volumeleaders-mcp
```

### Client configuration

<details>
<summary>Claude Code (.mcp.json)</summary>

Create `.mcp.json` in your project root.

**Using uv:**

```json
{
  "mcpServers": {
    "volumeleaders": {
      "type": "stdio",
      "command": "uv",
      "args": ["run", "--with", "volumeleaders[mcp]", "volumeleaders-mcp"]
    }
  }
}
```

After adding the config, restart Claude Code and run `/mcp` to verify the server appears.

</details>

<details>
<summary>OpenCode (opencode.json)</summary>

Add to `opencode.json` (or `opencode.jsonc`) in your project root.

**Using uv:**

```jsonc
{
  "mcp": {
    "volumeleaders": {
      "type": "local",
      "command": ["uv", "run", "--with", "volumeleaders[mcp]", "volumeleaders-mcp"]
    }
  }
}
```


</details>

## License

MIT
