"""Behavioral tests for client request methods and lifecycle management."""

from functools import partial
from importlib import import_module
from typing import Any
from unittest.mock import Mock

import httpx
import pytest

_auth = import_module("volumeleaders._auth")
_client_module = import_module("volumeleaders._client")
_exceptions = import_module("volumeleaders._exceptions")


def test_post_form_returns_parsed_json(
    mock_client: tuple[Any, Mock],
) -> None:
    """Send form-encoded bodies and return the parsed JSON response."""
    client, http_mock = mock_client
    response = Mock(status_code=200)
    response.json.return_value = {"ok": True}
    http_mock.post.return_value = response

    assert client.post_form("/form", "StartDate=2026-01-01") == {"ok": True}


def test_post_datatables_raw_returns_full_envelope(
    mock_client: tuple[Any, Mock],
) -> None:
    """Return the complete DataTables envelope for pagination metadata."""
    client, http_mock = mock_client
    payload = {"data": [{"Ticker": "SPY"}], "recordsTotal": 1}
    response = Mock(status_code=200)
    response.json.return_value = payload
    http_mock.post.return_value = response

    assert client.post_datatables_raw("/table", "draw=1") == payload


def test_request_failure_is_wrapped_as_api_error(
    mock_client: tuple[Any, Mock],
) -> None:
    """Wrap transport failures in APIError."""
    client, http_mock = mock_client
    http_mock.post.side_effect = httpx.ConnectError("offline")

    with pytest.raises(_exceptions.APIError, match="offline"):
        client.post_json("/json", {})


def test_client_lifecycle_attaches_auth_and_closes_transport(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Attach auth state to requests and close the transport on exit."""
    captured: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        captured.append(request)
        return httpx.Response(200, json={"ok": True})

    # Inject a mock transport while keeping the real httpx.Client behavior
    # for headers, cookies, and closed-state handling.
    monkeypatch.setattr(
        _client_module.httpx,
        "Client",
        partial(httpx.Client, transport=httpx.MockTransport(handler)),
    )

    def fake_extract_cookies(_browser: str) -> dict[str, str]:
        return {"ASP.NET_SessionId": "session", ".ASPXAUTH": "auth"}

    def fake_fetch_xsrf_token(
        _http_client: httpx.Client,
        _cookies: dict[str, str],
    ) -> str:
        return "xsrf-token"

    monkeypatch.setattr(_client_module, "extract_cookies", fake_extract_cookies)
    monkeypatch.setattr(_client_module, "fetch_xsrf_token", fake_fetch_xsrf_token)

    with _client_module.VolumeLeadersClient(timeout=12) as client:
        assert client.post_json("/json", {"value": 1}) == {"ok": True}

    request = captured[0]
    assert request.url.path == "/json"
    assert request.headers["x-xsrf-token"] == "xsrf-token"
    assert request.headers["x-requested-with"] == "XMLHttpRequest"
    assert request.headers["user-agent"] == _auth.USER_AGENT
    assert "ASP.NET_SessionId=session" in request.headers["cookie"]
    assert ".ASPXAUTH=auth" in request.headers["cookie"]

    with pytest.raises(RuntimeError, match="closed"):
        client.post_json("/json", {})
