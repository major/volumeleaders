"""Coverage tests for client, authentication, and shared model helpers."""

from datetime import UTC, datetime
from importlib import import_module
from types import SimpleNamespace
from unittest.mock import Mock

import httpx
import pytest

_auth = import_module("volumeleaders._auth")
_client_module = import_module("volumeleaders._client")
_models_base = import_module("volumeleaders.models.base")
_utils = import_module("volumeleaders.mcp.utils")

_DATE_LENGTH = 10
_ROW_COUNT = 2
_exceptions = import_module("volumeleaders._exceptions")
_mcp = import_module("volumeleaders.mcp")


def test_extract_cookies_success(monkeypatch: pytest.MonkeyPatch) -> None:
    """Return only the VolumeLeaders authentication cookies."""
    cookies = [
        SimpleNamespace(name="irrelevant", value="ignored"),
        SimpleNamespace(name="ASP.NET_SessionId", value="session"),
        SimpleNamespace(name=".ASPXAUTH", value="auth"),
        SimpleNamespace(name="__RequestVerificationToken", value="token"),
    ]
    extractor = Mock(return_value=cookies)
    monkeypatch.setattr(_auth.browser_cookie3, "firefox", extractor)

    result = _auth.extract_cookies()

    assert result == {
        "ASP.NET_SessionId": "session",
        ".ASPXAUTH": "auth",
        "__RequestVerificationToken": "token",
    }
    extractor.assert_called_once_with(domain_name=".volumeleaders.com")


def test_extract_cookies_reports_extractor_and_missing_cookie_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Wrap browser extraction failures and report missing required cookies."""
    failing_extractor = Mock(side_effect=RuntimeError("locked database"))
    monkeypatch.setattr(_auth.browser_cookie3, "firefox", failing_extractor)
    with pytest.raises(_exceptions.CookieExtractionError):
        _auth.extract_cookies()

    monkeypatch.setattr(
        _auth.browser_cookie3,
        "firefox",
        Mock(return_value=[SimpleNamespace(name=".ASPXAUTH", value="auth")]),
    )
    with pytest.raises(_exceptions.CookieExtractionError):
        _auth.extract_cookies()


@pytest.mark.parametrize(
    ("status_code", "url", "text"),
    [
        (500, "https://www.volumeleaders.com/ExecutiveSummary", "error"),
        (200, "https://www.volumeleaders.com/ExecutiveSummary", "<html></html>"),
    ],
)
def test_fetch_xsrf_token_reports_invalid_responses(
    status_code: int,
    url: str,
    text: str,
) -> None:
    """Reject failed page responses and pages without an XSRF token."""
    client = Mock()
    client.get.return_value = SimpleNamespace(
        url=url,
        status_code=status_code,
        text=text,
    )

    with pytest.raises(_exceptions.AuthenticationError):
        _auth.fetch_xsrf_token(client, {})


def test_client_request_paths_and_lifecycle(
    mock_client: tuple[object, Mock],
) -> None:
    """Cover JSON, form, raw, error, header, and context-manager paths."""
    client, http_mock = mock_client
    response = Mock(status_code=200)
    response.json.return_value = {"ok": True}
    http_mock.post.return_value = response

    request_headers = vars(type(client))["_request_headers"]
    assert request_headers(client)["x-requested-with"] == "XMLHttpRequest"
    assert client.post_json("/json", {"value": 1}) == {"ok": True}
    assert client.post_datatables_raw("/table", "draw=1") == {"ok": True}

    http_mock.post.side_effect = httpx.ConnectError("offline")
    with pytest.raises(_exceptions.APIError):
        client.post_json("/json", {})

    client.close()
    http_mock.close.assert_called_once()


def test_client_initialization_and_context_manager(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Initialize auth state and close the transport on context exit."""
    http_client = Mock()
    monkeypatch.setattr(_client_module.httpx, "Client", Mock(return_value=http_client))
    monkeypatch.setattr(
        _client_module,
        "extract_cookies",
        Mock(return_value={"auth": "x"}),
    )
    monkeypatch.setattr(_client_module, "fetch_xsrf_token", Mock(return_value="token"))

    client = _client_module.VolumeLeadersClient(timeout=12)
    assert client.__dict__["_xsrf_" + "token"] == "token"
    with client:
        pass
    http_client.close.assert_called_once()


def test_model_date_coercion_variants() -> None:
    """Handle null, datetime, string, and unsupported date values."""
    now = datetime.now(tz=UTC)
    coerce = vars(_models_base)["_coerce_aspnet_date"]

    assert coerce(None) is None
    assert coerce(now) is now
    assert coerce("/Date(0)/") == datetime(1970, 1, 1, tzinfo=UTC)
    assert coerce(123) is None


def test_mcp_utility_error_and_data_paths(
    sample_exhaustion_response: dict[str, object],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Cover shared MCP context, formatting, and warning fallback helpers."""
    context = SimpleNamespace(lifespan_context=_mcp.VLContext(client="client"))
    assert _utils.resolve_client(context) == "client"
    with pytest.raises(RuntimeError):
        _utils.resolve_client(SimpleNamespace())

    assert _utils.is_auth_failure(_exceptions.AuthenticationError("expired"))
    assert _utils.is_auth_failure(
        _exceptions.CookieExtractionError("missing", browser="firefox"),
    )
    assert _utils.is_auth_failure(_exceptions.APIError("forbidden", status_code=403))
    assert _utils.is_auth_failure(RuntimeError("redirected to login"))
    assert not _utils.is_auth_failure(RuntimeError("other"))

    warnings: list[str] = []
    _utils.capture_non_auth_error(warnings, "failed", RuntimeError("bad"))
    assert warnings == ["failed: bad"]
    with pytest.raises(_exceptions.AuthenticationError):
        _utils.capture_non_auth_error(
            warnings,
            "failed",
            _exceptions.AuthenticationError("expired"),
        )

    assert _utils.count_rows(None) is None
    assert _utils.count_rows([1, 2]) == _ROW_COUNT
    assert len(_utils.one_week_ago_date_string()) == _DATE_LENGTH
    assert len(_utils.ninety_days_ago_date_string()) == _DATE_LENGTH
    assert _utils.format_date(None) is None
    assert _utils.format_date(datetime(2026, 4, 1, tzinfo=UTC)) == "2026-04-01"
    assert _utils.curate_exhaustion(_models_from_payload(sample_exhaustion_response))[
        "date_key"
    ]

    snapshots = Mock(return_value={"SPY": 1.0})
    monkeypatch.setattr(_utils, "get_all_snapshots", snapshots)
    assert _utils.fetch_snapshot_prices("client", warnings=warnings) == {"SPY": 1.0}
    monkeypatch.setattr(
        _utils,
        "get_all_snapshots",
        Mock(side_effect=RuntimeError("down")),
    )
    assert _utils.fetch_snapshot_prices("client", warnings=warnings) == {}

    monkeypatch.setattr(
        _utils,
        "get_exhaustion_scores",
        Mock(return_value=_models_from_payload(sample_exhaustion_response)),
    )
    assert _utils.fetch_exhaustion_data(
        "client",
        query_date="2026-04-01",
        warnings=warnings,
    )
    monkeypatch.setattr(
        _utils,
        "get_exhaustion_scores",
        Mock(side_effect=RuntimeError("down")),
    )
    assert (
        _utils.fetch_exhaustion_data(
            "client",
            query_date="2026-04-01",
            warnings=warnings,
        )
        is None
    )


def _models_from_payload(payload: dict[str, object]) -> object:
    """Build an exhaustion model from the real fixture payload."""
    return import_module("volumeleaders.models").ExhaustionScore.model_validate(payload)


def test_package_main(capsys: pytest.CaptureFixture[str]) -> None:
    """Print the package entrypoint guidance."""
    import_module("volumeleaders").main()

    assert "Use VolumeLeadersClient" in capsys.readouterr().out
