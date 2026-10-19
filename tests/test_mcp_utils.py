"""Behavioral tests for shared MCP utility helpers."""

from datetime import UTC, date, datetime, timedelta
from importlib import import_module
from types import SimpleNamespace
from typing import Any
from unittest.mock import Mock

import pytest

_exceptions = import_module("volumeleaders._exceptions")
_mcp = import_module("volumeleaders.mcp")
_models = import_module("volumeleaders.models")
_utils = import_module("volumeleaders.mcp.utils")

_DATE_TOLERANCE_DAYS = 1


def test_resolve_client_returns_existing_client() -> None:
    """Reuse the client already stored on the lifespan context."""
    existing = SimpleNamespace(name="existing")
    context = SimpleNamespace(lifespan_context=_mcp.VLContext(client=existing))

    assert _utils.resolve_client(context) is existing


def test_resolve_client_requires_lifespan_context() -> None:
    """Reject contexts that do not carry a VLContext holder."""
    with pytest.raises(TypeError, match="lifespan context"):
        _utils.resolve_client(SimpleNamespace())


def test_resolve_client_creates_and_reuses_client(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Create the client lazily once and cache it for later calls."""
    created = SimpleNamespace(name="created")
    construction_count = 0

    def fake_constructor() -> SimpleNamespace:
        nonlocal construction_count
        construction_count += 1
        return created

    monkeypatch.setattr(_utils, "VolumeLeadersClient", fake_constructor)
    holder = _mcp.VLContext()
    context = SimpleNamespace(lifespan_context=holder)

    assert _utils.resolve_client(context) is created
    assert _utils.resolve_client(context) is created
    assert construction_count == 1
    assert holder.client is created


@pytest.mark.parametrize(
    "error",
    [
        pytest.param(_exceptions.AuthenticationError("expired"), id="auth_error"),
        pytest.param(
            _exceptions.CookieExtractionError("missing", browser="firefox"),
            id="cookie_error",
        ),
        pytest.param(
            _exceptions.APIError("forbidden", status_code=403),
            id="forbidden",
        ),
        pytest.param(
            _exceptions.APIError("unauthorized", status_code=401),
            id="unauthorized",
        ),
        pytest.param(RuntimeError("redirected to login"), id="login_message"),
    ],
)
def test_is_auth_failure_detects_auth_problems(error: Exception) -> None:
    """Treat auth exceptions and login redirects as auth failures."""
    assert _utils.is_auth_failure(error)


@pytest.mark.parametrize(
    "error",
    [
        pytest.param(
            _exceptions.APIError("server error", status_code=500),
            id="server_error",
        ),
        pytest.param(RuntimeError("connection reset"), id="unrelated"),
    ],
)
def test_is_auth_failure_ignores_unrelated_errors(error: Exception) -> None:
    """Do not classify unrelated failures as auth problems."""
    assert not _utils.is_auth_failure(error)


def test_capture_non_auth_error_appends_warning() -> None:
    """Record unrelated failures as warnings."""
    warnings: list[str] = []

    _utils.capture_non_auth_error(warnings, "Failed to fetch", RuntimeError("down"))

    assert warnings == ["Failed to fetch: down"]


def test_capture_non_auth_error_reraises_auth_failures() -> None:
    """Let auth failures propagate instead of recording warnings."""
    warnings: list[str] = []

    with pytest.raises(_exceptions.AuthenticationError, match="expired"):
        _utils.capture_non_auth_error(
            warnings,
            "Failed to fetch",
            _exceptions.AuthenticationError("expired"),
        )

    assert warnings == []


@pytest.mark.parametrize(
    ("rows", "expected"),
    [
        pytest.param(None, None, id="missing"),
        pytest.param([], 0, id="empty"),
        pytest.param([1, 2], 2, id="populated"),
    ],
)
def test_count_rows(rows: list[int] | None, expected: int | None) -> None:
    """Return the row count only when rows are present."""
    assert _utils.count_rows(rows) == expected


def test_relative_date_helpers_return_iso_dates() -> None:
    """Return YYYY-MM-DD dates offset by the documented amount."""
    today = datetime.now(tz=UTC).date()
    one_week = date.fromisoformat(_utils.one_week_ago_date_string())
    ninety_days = date.fromisoformat(_utils.ninety_days_ago_date_string())

    week_offset = one_week - (today - timedelta(weeks=1))
    ninety_day_offset = ninety_days - (today - timedelta(days=90))

    assert abs(week_offset.days) <= _DATE_TOLERANCE_DAYS
    assert abs(ninety_day_offset.days) <= _DATE_TOLERANCE_DAYS


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        pytest.param(None, None, id="missing"),
        pytest.param(datetime(2026, 4, 1, tzinfo=UTC), "2026-04-01", id="datetime"),
    ],
)
def test_format_date(value: datetime | None, expected: str | None) -> None:
    """Format optional datetimes as ISO dates."""
    assert _utils.format_date(value) == expected


@pytest.mark.parametrize(
    ("datekey", "expected"),
    [
        pytest.param(20260819, "2026-08-19", id="integer"),
        pytest.param("20260819", "2026-08-19", id="string"),
        pytest.param(" 20260819 ", "2026-08-19", id="padded_string"),
        pytest.param("invalid", "invalid", id="unrecognized"),
        pytest.param("2026081", "2026081", id="short_value"),
    ],
)
def test_format_datekey_to_iso(datekey: int | str, expected: str) -> None:
    """Convert YYYYMMDD date keys to ISO dates, passing others through."""
    assert _utils.format_datekey_to_iso(datekey) == expected


def test_curate_exhaustion_returns_compact_scores(
    sample_exhaustion_response: dict[str, Any],
) -> None:
    """Expose the high-signal exhaustion fields for MCP responses."""
    exhaustion = _models.ExhaustionScore.model_validate(sample_exhaustion_response)

    assert _utils.curate_exhaustion(exhaustion) == {
        "date_key": exhaustion.date_key,
        "exhaustion_score_rank": exhaustion.exhaustion_score_rank,
        "exhaustion_score_rank_30_day": exhaustion.exhaustion_score_rank_30_day,
        "exhaustion_score_rank_90_day": exhaustion.exhaustion_score_rank_90_day,
        "exhaustion_score_rank_365_day": exhaustion.exhaustion_score_rank_365_day,
    }


def test_fetch_snapshot_prices_returns_snapshot_map(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return the snapshot price map when the endpoint succeeds."""
    monkeypatch.setattr(_utils, "get_all_snapshots", Mock(return_value={"SPY": 1.0}))
    warnings: list[str] = []

    assert _utils.fetch_snapshot_prices("client", warnings=warnings) == {"SPY": 1.0}
    assert warnings == []


def test_fetch_snapshot_prices_returns_empty_map_on_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return an empty map and record a warning when the endpoint fails."""
    monkeypatch.setattr(
        _utils,
        "get_all_snapshots",
        Mock(side_effect=RuntimeError("down")),
    )
    warnings: list[str] = []

    assert _utils.fetch_snapshot_prices("client", warnings=warnings) == {}
    assert warnings == ["Failed to fetch snapshot prices: down"]


def test_fetch_exhaustion_data_returns_curated_scores(
    sample_exhaustion_response: dict[str, Any],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return curated exhaustion scores when the endpoint succeeds."""
    exhaustion = _models.ExhaustionScore.model_validate(sample_exhaustion_response)
    monkeypatch.setattr(
        _utils,
        "get_exhaustion_scores",
        Mock(return_value=exhaustion),
    )
    warnings: list[str] = []

    result = _utils.fetch_exhaustion_data(
        "client",
        query_date="2026-04-01",
        warnings=warnings,
    )

    assert result == {
        "date_key": exhaustion.date_key,
        "exhaustion_score_rank": exhaustion.exhaustion_score_rank,
        "exhaustion_score_rank_30_day": exhaustion.exhaustion_score_rank_30_day,
        "exhaustion_score_rank_90_day": exhaustion.exhaustion_score_rank_90_day,
        "exhaustion_score_rank_365_day": exhaustion.exhaustion_score_rank_365_day,
    }
    assert warnings == []


def test_fetch_exhaustion_data_returns_none_on_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Return None and record a warning when the endpoint fails."""
    monkeypatch.setattr(
        _utils,
        "get_exhaustion_scores",
        Mock(side_effect=RuntimeError("down")),
    )
    warnings: list[str] = []

    result = _utils.fetch_exhaustion_data(
        "client",
        query_date="2026-04-01",
        warnings=warnings,
    )

    assert result is None
    assert warnings == ["Failed to fetch exhaustion scores: down"]
