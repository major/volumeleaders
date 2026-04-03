"""Tests for the trade_levels MCP tool."""

from __future__ import annotations

from importlib import import_module
from typing import Any
from unittest.mock import Mock

import pytest

_mcp_module = import_module("volumeleaders.mcp")
_tools = import_module("volumeleaders.mcp.tools.trade_levels")
_models = import_module("volumeleaders.models")

trade_levels_tool = _tools.trade_levels
TradeLevel = _models.TradeLevel

_curate_level = _tools._curate_level
_get_current_price = _tools._get_current_price

_FAKE_CURRENT_PRICE = 23.50


@pytest.fixture(autouse=True)
def _stub_get_company(monkeypatch: pytest.MonkeyPatch) -> None:
    """Stub get_company so integration tests don't make real API calls."""
    company = Mock(current_price=_FAKE_CURRENT_PRICE)
    monkeypatch.setattr(_tools, "get_company", lambda *a, **kw: company)
    monkeypatch.setattr(_tools, "get_all_snapshots", lambda *a, **kw: {})


def _make_levels(
    sample_trade_level_response: dict[str, Any],
) -> list[Any]:
    """Build TradeLevel model rows from the real API fixture."""
    return [
        TradeLevel.model_validate(row) for row in sample_trade_level_response["data"]
    ]


# -- _curate_level -------------------------------------------------------------


def test_curate_level_field_set(
    sample_trade_level_response: dict[str, Any],
) -> None:
    """Return exactly the expected compact fields from TradeLevel model."""
    level = TradeLevel.model_validate(sample_trade_level_response["data"][0])
    result = _curate_level(level)

    assert set(result) == {
        "price",
        "dollars",
        "volume",
        "trades",
        "rank",
        "relative_size",
        "cumulative_distribution",
        "level_origin_date",
        "level_last_confirmed",
    }


def test_curate_level_preserves_values(
    sample_trade_level_response: dict[str, Any],
) -> None:
    """Map model attributes to curated dict values correctly."""
    level = TradeLevel.model_validate(sample_trade_level_response["data"][0])
    result = _curate_level(level)

    assert result["price"] == level.price
    assert result["dollars"] == "$166.5M"
    assert result["volume"] == level.volume
    assert result["trades"] == level.trades
    assert result["rank"] == level.trade_level_rank
    assert result["relative_size"] == level.relative_size
    assert result["cumulative_distribution"] == level.cumulative_distribution


def test_curate_level_dollars_formatted(
    sample_trade_level_response: dict[str, Any],
) -> None:
    """Format dollars as a compact human-readable string."""
    level = TradeLevel.model_validate(sample_trade_level_response["data"][0])
    result = _curate_level(level)

    # Fixture has Dollars: 166529945.86; formatted to "$166.5M".
    assert isinstance(result["dollars"], str)
    assert result["dollars"] == "$166.5M"


def test_curate_level_dates(
    sample_trade_level_response: dict[str, Any],
) -> None:
    """Format min_date and max_date as self-documenting level date fields."""
    level = TradeLevel.model_validate(sample_trade_level_response["data"][0])
    result = _curate_level(level)

    # Fixture MinDate: /Date(1709251200000)/ -> 2024-03-01
    # Fixture MaxDate: /Date(1775088000000)/ -> 2026-04-02
    assert result["level_origin_date"] == "2024-03-01"
    assert result["level_last_confirmed"] == "2026-04-02"


def test_curate_level_omits_removed_fields(
    sample_trade_level_response: dict[str, Any],
) -> None:
    """Exclude fields dropped for token efficiency."""
    level = TradeLevel.model_validate(sample_trade_level_response["data"][0])
    result = _curate_level(level)

    assert "ticker" not in result
    assert "name" not in result
    assert "dates" not in result  # replaced by level_origin_date/level_last_confirmed
    assert "trade_level_rank" not in result  # renamed to "rank"


# -- Tool integration tests ----------------------------------------------------


def test_envelope_shape_default(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_level_response: dict[str, Any],
    mcp_context: Any,
) -> None:
    """Return minimal envelope by default: data and metadata only."""
    levels = _make_levels(sample_trade_level_response)
    monkeypatch.setattr(_tools, "get_trade_levels", lambda *a, **kw: levels)

    result = trade_levels_tool(ticker="AMD", end_date="2026-04-02", ctx=mcp_context)

    # No warnings when endpoint succeeds.
    assert set(result) == {"data", "metadata"}
    assert set(result["data"]) == {"levels"}
    assert set(result["metadata"]) == {"level_count", "current_price"}


def test_envelope_omits_warnings_when_empty(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_level_response: dict[str, Any],
    mcp_context: Any,
) -> None:
    """Omit the warnings key entirely when there are no warnings."""
    levels = _make_levels(sample_trade_level_response)
    monkeypatch.setattr(_tools, "get_trade_levels", lambda *a, **kw: levels)

    result = trade_levels_tool(ticker="AMD", end_date="2026-04-02", ctx=mcp_context)

    assert "warnings" not in result


def test_envelope_includes_warnings_when_present(
    monkeypatch: pytest.MonkeyPatch,
    mcp_context: Any,
) -> None:
    """Include warnings key when endpoint fails."""
    monkeypatch.setattr(
        _tools,
        "get_trade_levels",
        Mock(side_effect=RuntimeError("Server error")),
    )

    result = trade_levels_tool(ticker="AMD", end_date="2026-04-02", ctx=mcp_context)

    assert "warnings" in result
    assert any("Failed to fetch trade levels" in w for w in result["warnings"])


def test_curated_fields_in_response(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_level_response: dict[str, Any],
    mcp_context: Any,
) -> None:
    """Curate level rows to the expected compact field set in tool response."""
    levels = _make_levels(sample_trade_level_response)
    monkeypatch.setattr(_tools, "get_trade_levels", lambda *a, **kw: levels)

    result = trade_levels_tool(ticker="AMD", end_date="2026-04-02", ctx=mcp_context)

    assert result["data"]["levels"] is not None
    assert len(result["data"]["levels"]) == 6
    assert set(result["data"]["levels"][0]) == {
        "price",
        "dollars",
        "volume",
        "trades",
        "rank",
        "relative_size",
        "cumulative_distribution",
        "level_origin_date",
        "level_last_confirmed",
        "proximity_pct",
    }


def test_default_dates(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_level_response: dict[str, Any],
    mcp_context: Any,
) -> None:
    """Default end_date to today and start_date to one year ago."""
    captured_kwargs: dict[str, Any] = {}

    def fake_endpoint(*args: Any, **kwargs: Any) -> list[Any]:
        """Capture endpoint kwargs for assertion."""
        captured_kwargs.update(kwargs)
        return _make_levels(sample_trade_level_response)

    monkeypatch.setattr(_tools, "get_trade_levels", fake_endpoint)
    monkeypatch.setattr(_tools, "today_date_string", lambda: "2026-04-02")
    monkeypatch.setattr(_tools, "one_year_ago_date_string", lambda: "2025-04-02")

    trade_levels_tool(ticker="AMD", ctx=mcp_context)

    assert captured_kwargs["start_date"] == "2025-04-02"
    assert captured_kwargs["end_date"] == "2026-04-02"


def test_explicit_dates_used(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_level_response: dict[str, Any],
    mcp_context: Any,
) -> None:
    """Use explicit dates when provided."""
    captured_kwargs: dict[str, Any] = {}

    def fake_endpoint(*args: Any, **kwargs: Any) -> list[Any]:
        """Capture endpoint kwargs for assertion."""
        captured_kwargs.update(kwargs)
        return _make_levels(sample_trade_level_response)

    monkeypatch.setattr(_tools, "get_trade_levels", fake_endpoint)

    trade_levels_tool(
        ticker="AMD",
        start_date="2025-01-01",
        end_date="2026-03-15",
        ctx=mcp_context,
    )

    assert captured_kwargs["start_date"] == "2025-01-01"
    assert captured_kwargs["end_date"] == "2026-03-15"


def test_ticker_passed_to_endpoint(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_level_response: dict[str, Any],
    mcp_context: Any,
) -> None:
    """Pass ticker through to the endpoint function."""
    captured_kwargs: dict[str, Any] = {}

    def fake_endpoint(*args: Any, **kwargs: Any) -> list[Any]:
        """Capture endpoint kwargs for assertion."""
        captured_kwargs.update(kwargs)
        return _make_levels(sample_trade_level_response)

    monkeypatch.setattr(_tools, "get_trade_levels", fake_endpoint)

    trade_levels_tool(ticker="AMD", end_date="2026-04-02", ctx=mcp_context)

    assert captured_kwargs["ticker"] == "AMD"


def test_dates_passed_to_endpoint(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_level_response: dict[str, Any],
    mcp_context: Any,
) -> None:
    """Pass start_date and end_date through to the endpoint function."""
    captured_kwargs: dict[str, Any] = {}

    def fake_endpoint(*args: Any, **kwargs: Any) -> list[Any]:
        """Capture endpoint kwargs for assertion."""
        captured_kwargs.update(kwargs)
        return _make_levels(sample_trade_level_response)

    monkeypatch.setattr(_tools, "get_trade_levels", fake_endpoint)

    trade_levels_tool(
        ticker="AMD",
        start_date="2025-04-02",
        end_date="2026-04-02",
        ctx=mcp_context,
    )

    assert captured_kwargs["start_date"] == "2025-04-02"
    assert captured_kwargs["end_date"] == "2026-04-02"


def test_endpoint_failure_returns_null_with_warning(
    monkeypatch: pytest.MonkeyPatch,
    mcp_context: Any,
) -> None:
    """Return levels as null with a warning when endpoint fails."""
    monkeypatch.setattr(
        _tools,
        "get_trade_levels",
        Mock(side_effect=RuntimeError("Server error")),
    )

    result = trade_levels_tool(ticker="AMD", end_date="2026-04-02", ctx=mcp_context)

    assert result["data"]["levels"] is None
    assert any("Failed to fetch trade levels" in w for w in result["warnings"])


def test_empty_result_returns_empty_list(
    monkeypatch: pytest.MonkeyPatch,
    mcp_context: Any,
) -> None:
    """Return empty levels list when endpoint returns no rows."""
    monkeypatch.setattr(_tools, "get_trade_levels", lambda *a, **kw: [])

    result = trade_levels_tool(ticker="AMD", end_date="2026-04-02", ctx=mcp_context)

    assert result["data"]["levels"] == []
    assert result["metadata"]["level_count"] == 0


def test_metadata_counts(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_level_response: dict[str, Any],
    mcp_context: Any,
) -> None:
    """Include accurate level count in metadata."""
    levels = _make_levels(sample_trade_level_response)
    monkeypatch.setattr(_tools, "get_trade_levels", lambda *a, **kw: levels)

    result = trade_levels_tool(ticker="AMD", end_date="2026-04-02", ctx=mcp_context)

    assert result["metadata"]["level_count"] == 6


def test_metadata_null_on_failure(
    monkeypatch: pytest.MonkeyPatch,
    mcp_context: Any,
) -> None:
    """Return null metadata when endpoint fails."""
    monkeypatch.setattr(
        _tools,
        "get_trade_levels",
        Mock(side_effect=RuntimeError("Timeout")),
    )

    result = trade_levels_tool(ticker="AMD", end_date="2026-04-02", ctx=mcp_context)

    assert result["metadata"]["level_count"] is None


def test_proximity_pct_computed_from_current_price(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_level_response: dict[str, Any],
    mcp_context: Any,
) -> None:
    """Enrich levels with proximity_pct relative to current price."""
    levels = _make_levels(sample_trade_level_response)
    monkeypatch.setattr(_tools, "get_trade_levels", lambda *a, **kw: levels)

    result = trade_levels_tool(ticker="AMD", end_date="2026-04-02", ctx=mcp_context)

    first_level = result["data"]["levels"][0]
    assert "proximity_pct" in first_level
    # proximity_pct = (level_price - current_price) / current_price * 100
    expected = round(
        (first_level["price"] - _FAKE_CURRENT_PRICE) / _FAKE_CURRENT_PRICE * 100,
        2,
    )
    assert first_level["proximity_pct"] == expected


def test_proximity_pct_absent_when_no_current_price(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_level_response: dict[str, Any],
    mcp_context: Any,
) -> None:
    """Omit proximity_pct when current price is unavailable."""
    levels = _make_levels(sample_trade_level_response)
    monkeypatch.setattr(_tools, "get_trade_levels", lambda *a, **kw: levels)
    monkeypatch.setattr(
        _tools,
        "get_company",
        Mock(side_effect=RuntimeError("fail")),
    )
    monkeypatch.setattr(
        _tools,
        "get_all_snapshots",
        Mock(side_effect=RuntimeError("fail")),
    )

    result = trade_levels_tool(ticker="AMD", end_date="2026-04-02", ctx=mcp_context)

    assert "proximity_pct" not in result["data"]["levels"][0]


def test_metadata_includes_current_price(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_level_response: dict[str, Any],
    mcp_context: Any,
) -> None:
    """Include the ticker's current price in metadata."""
    levels = _make_levels(sample_trade_level_response)
    monkeypatch.setattr(_tools, "get_trade_levels", lambda *a, **kw: levels)

    result = trade_levels_tool(ticker="AMD", end_date="2026-04-02", ctx=mcp_context)

    assert result["metadata"]["current_price"] == _FAKE_CURRENT_PRICE


def test_get_current_price_falls_back_to_snapshots_when_company_price_null(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Use the all-snapshots endpoint when company metadata has a null price."""
    monkeypatch.setattr(
        _tools, "get_company", lambda *a, **kw: Mock(current_price=None)
    )
    monkeypatch.setattr(
        _tools,
        "get_all_snapshots",
        lambda *a, **kw: {"AMD": 209.95, "SPY": 655.01},
    )

    warnings: list[str] = []

    assert _get_current_price(Mock(), "AMD", warnings) == 209.95
    assert warnings == []


def test_metadata_falls_back_to_snapshots_when_company_price_null(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_level_response: dict[str, Any],
    mcp_context: Any,
) -> None:
    """Populate metadata current_price from snapshots when company price is null."""
    levels = _make_levels(sample_trade_level_response)
    monkeypatch.setattr(_tools, "get_trade_levels", lambda *a, **kw: levels)
    monkeypatch.setattr(
        _tools, "get_company", lambda *a, **kw: Mock(current_price=None)
    )
    monkeypatch.setattr(
        _tools,
        "get_all_snapshots",
        lambda *a, **kw: {"AMD": 209.95},
    )

    result = trade_levels_tool(ticker="AMD", end_date="2026-04-02", ctx=mcp_context)

    assert result["metadata"]["current_price"] == 209.95


def test_current_price_failure_warns(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_level_response: dict[str, Any],
    mcp_context: Any,
) -> None:
    """Warn and return null current_price when both lookup paths fail."""
    levels = _make_levels(sample_trade_level_response)
    monkeypatch.setattr(_tools, "get_trade_levels", lambda *a, **kw: levels)
    monkeypatch.setattr(
        _tools,
        "get_company",
        Mock(side_effect=RuntimeError("Company lookup failed")),
    )
    monkeypatch.setattr(
        _tools,
        "get_all_snapshots",
        Mock(side_effect=RuntimeError("Snapshot lookup failed")),
    )

    result = trade_levels_tool(ticker="AMD", end_date="2026-04-02", ctx=mcp_context)

    assert result["metadata"]["current_price"] is None
    assert any(
        "Failed to fetch current price from company metadata" in w
        for w in result["warnings"]
    )
    assert any(
        "Failed to fetch current price from snapshots" in w for w in result["warnings"]
    )
    # Levels should still be returned even if current price fails.
    assert result["data"]["levels"] is not None
    assert len(result["data"]["levels"]) == 6


def test_current_price_company_failure_uses_snapshots_without_warning(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_level_response: dict[str, Any],
    mcp_context: Any,
) -> None:
    """Recover current price from snapshots when company lookup raises."""
    levels = _make_levels(sample_trade_level_response)
    monkeypatch.setattr(_tools, "get_trade_levels", lambda *a, **kw: levels)
    monkeypatch.setattr(
        _tools,
        "get_company",
        Mock(side_effect=RuntimeError("Company lookup failed")),
    )
    monkeypatch.setattr(_tools, "get_all_snapshots", lambda *a, **kw: {"AMD": 209.95})

    result = trade_levels_tool(ticker="AMD", end_date="2026-04-02", ctx=mcp_context)

    assert result["metadata"]["current_price"] == 209.95
    assert "warnings" not in result


@pytest.mark.asyncio
async def test_fastmcp_client_transport(
    monkeypatch: pytest.MonkeyPatch,
    sample_trade_level_response: dict[str, Any],
) -> None:
    """Call the registered tool through FastMCP client transport."""
    from fastmcp import Client

    class _FakeClient:
        """Test client object used for lifespan initialization."""

        def close(self) -> None:
            """Provide the close method expected by lifespan cleanup."""

    levels = _make_levels(sample_trade_level_response)
    monkeypatch.setattr(_tools, "get_trade_levels", lambda *a, **kw: levels)
    monkeypatch.setattr(_mcp_module, "VolumeLeadersClient", _FakeClient)

    async with Client(_mcp_module.mcp) as client:
        result = await client.call_tool(
            "trade_levels",
            {"ticker": "AMD", "end_date": "2026-04-02"},
        )

    assert result.data is not None
    assert result.data["data"]["levels"] is not None
