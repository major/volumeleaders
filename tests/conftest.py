"""Shared test fixtures for real API response payloads."""

import json
import sys
from importlib import import_module
from pathlib import Path
from typing import Any
from unittest.mock import Mock

import pytest

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SRC_ROOT = PROJECT_ROOT / "src"

if str(SRC_ROOT) not in sys.path:
    sys.path.insert(0, str(SRC_ROOT))


def _fixtures_dir() -> Path:
    """Return the absolute path to the test fixtures directory."""
    return Path(__file__).resolve().parent / "fixtures"


def _load_json_file(file_name: str) -> object:
    """Load and parse a JSON fixture file."""
    return json.loads((_fixtures_dir() / file_name).read_text(encoding="utf-8"))


def _load_json_list(file_name: str) -> list[dict[str, Any]]:
    """Load and parse a JSON fixture file expecting a list of dictionaries."""
    data = _load_json_file(file_name)
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    return []


@pytest.fixture
def sample_trade_response() -> dict[str, Any]:
    """Return parsed trade DataTables response payload."""
    return _load_json_file("response_trades.json")


@pytest.fixture
def sample_trade_cluster_response() -> dict[str, Any]:
    """Return parsed trade cluster DataTables response payload."""
    return _load_json_file("response_trade_clusters.json")


@pytest.fixture
def sample_trade_cluster_bomb_response() -> dict[str, Any]:
    """Return parsed trade cluster bomb DataTables response payload."""
    return _load_json_file("response_trade_cluster_bombs.json")


@pytest.fixture
def sample_exhaustion_response() -> dict[str, Any]:
    """Return parsed exhaustion score response payload."""
    return _load_json_file("response_exhaustion_scores.json")


@pytest.fixture
def sample_company_response() -> dict[str, Any]:
    """Return parsed company metadata response payload."""
    return _load_json_file("response_chart_get_company.json")


@pytest.fixture
def sample_snapshot_response() -> dict[str, Any]:
    """Return parsed chart snapshot response payload."""
    return _load_json_file("response_chart_get_snapshot.json")


@pytest.fixture
def sample_price_bar_response() -> list[Any]:
    """Return parsed price-volume bar response payload."""
    return _load_json_file("response_chart_price_volume.json")


@pytest.fixture
def sample_earnings_response() -> dict[str, Any]:
    """Return parsed earnings response payload."""
    return _load_json_file("response_earnings.json")


@pytest.fixture
def sample_institutional_volume_response() -> dict[str, Any]:
    """Return parsed institutional volume response payload."""
    return _load_json_file("response_institutional_volume_v2.json")


@pytest.fixture
def sample_trade_level_response() -> dict[str, Any]:
    """Return parsed trade level response payload."""
    return _load_json_file("response_trade_levels.json")


@pytest.fixture
def sample_trade_level_touch_response() -> dict[str, Any]:
    """Return parsed trade level touch response payload."""
    return _load_json_file("response_trade_level_touches.json")


@pytest.fixture
def sample_watchlist_config_response() -> dict[str, Any]:
    """Return parsed watchlist config response payload."""
    return _load_json_file("response_watchlist_configs.json")


@pytest.fixture
def sample_snapshot_string() -> str:
    """Return raw file contents for all-snapshots response."""
    return (_fixtures_dir() / "response_get_all_snapshots.json").read_text(
        encoding="utf-8",
    )


@pytest.fixture
def sample_sector_breakdown_response() -> list[dict[str, Any]]:
    """Return parsed sector breakdown response payload."""
    return _load_json_list("response_sector_breakdown.json")


@pytest.fixture
def sample_institutional_outliers_response() -> list[dict[str, Any]]:
    """Return parsed institutional outliers response payload."""
    return _load_json_list("response_institutional_outliers.json")


@pytest.fixture
def sample_sector_themes_response() -> list[dict[str, Any]]:
    """Return parsed sector theme notional response payload."""
    return _load_json_list("response_notional_by_sector_by_name.json")


@pytest.fixture
def sample_supply_demand_areas_response() -> list[dict[str, Any]]:
    """Return parsed supply demand areas response payload."""
    return _load_json_list("response_supply_demand_areas.json")


@pytest.fixture
def sample_sector_daily_returns_response() -> list[dict[str, Any]]:
    """Return parsed sector daily returns response payload."""
    return _load_json_list("response_sector_daily_returns.json")


@pytest.fixture
def sample_dark_pool_volume_report_response() -> list[dict[str, Any]]:
    """Return parsed dark pool volume report response payload."""
    return _load_json_list("response_dark_pool_volume_report.json")


@pytest.fixture
def mock_client() -> tuple[Any, Mock]:
    """Create a VolumeLeadersClient with mocked HTTP transport, bypassing auth."""
    _client_module = import_module("volumeleaders._client")
    client = object.__new__(_client_module.VolumeLeadersClient)
    http_mock = Mock()
    client.__dict__["_http"] = http_mock
    client.__dict__["_cookies"] = {"ASP.NET_SessionId": "session", ".ASPXAUTH": "auth"}
    client.__dict__["_xsrf_" + "token"] = "test-xsrf-token"
    return client, http_mock
