# volumeleaders

> **Unofficial.** This project is not affiliated with, endorsed by, or connected to [volumeleaders.com](https://www.volumeleaders.com) in any way.

Python client for [volumeleaders.com](https://www.volumeleaders.com) institutional block trade data.

Extracts auth cookies from your browser session and provides typed access to all VolumeLeaders API endpoints, returning Pydantic models.

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

All endpoint functions take a `VolumeLeadersClient` as the first argument and return typed Pydantic models.

## MCP Server

The library includes an [MCP](https://modelcontextprotocol.io/) server that exposes VolumeLeaders data as tools for AI coding assistants. Five tools are available: `trades`, `trade_clusters`, `trade_cluster_bombs`, `trade_levels`, and `trade_level_touches`.

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
