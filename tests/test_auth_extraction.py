"""Behavioral tests for cookie extraction and XSRF token retrieval."""

from importlib import import_module
from types import SimpleNamespace
from unittest.mock import Mock

import pytest

_auth = import_module("volumeleaders._auth")
_exceptions = import_module("volumeleaders._exceptions")


def _patch_firefox(
    monkeypatch: pytest.MonkeyPatch,
    cookies: list[SimpleNamespace],
) -> None:
    """Serve the given cookie jar from the Firefox extractor."""

    def fake_firefox(**_kwargs: object) -> list[SimpleNamespace]:
        return cookies

    monkeypatch.setattr(_auth.browser_cookie3, "firefox", fake_firefox)


def test_extract_cookies_returns_only_required_auth_cookies(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Filter the browser cookie jar down to the VolumeLeaders auth set."""
    cookies = [
        SimpleNamespace(name="irrelevant", value="ignored"),
        SimpleNamespace(name="ASP.NET_SessionId", value="session"),
        SimpleNamespace(name=".ASPXAUTH", value="auth"),
        SimpleNamespace(name="VLDeviceID", value="device"),
        SimpleNamespace(name="__RequestVerificationToken", value="token"),
    ]
    _patch_firefox(monkeypatch, cookies)

    result = _auth.extract_cookies()

    assert result == {
        "ASP.NET_SessionId": "session",
        ".ASPXAUTH": "auth",
        "VLDeviceID": "device",
        "__RequestVerificationToken": "token",
    }


def test_extract_cookies_reports_missing_vldeviceid(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Surface VLDeviceID as a missing required cookie."""
    cookies = [
        SimpleNamespace(name="ASP.NET_SessionId", value="session"),
        SimpleNamespace(name=".ASPXAUTH", value="auth"),
    ]
    _patch_firefox(monkeypatch, cookies)

    with pytest.raises(_exceptions.CookieExtractionError) as excinfo:
        _auth.extract_cookies()

    assert "VLDeviceID" in str(excinfo.value)


def test_extract_cookies_wraps_browser_extraction_failure(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Wrap unexpected browser extraction failures in CookieExtractionError."""

    def failing_firefox(**_kwargs: object) -> list[object]:
        msg = "locked database"
        raise RuntimeError(msg)

    monkeypatch.setattr(_auth.browser_cookie3, "firefox", failing_firefox)

    with pytest.raises(_exceptions.CookieExtractionError, match="locked database"):
        _auth.extract_cookies()


@pytest.mark.parametrize(
    ("status_code", "text"),
    [
        pytest.param(500, "error", id="server_error"),
        pytest.param(200, "<html></html>", id="missing_token"),
    ],
)
def test_fetch_xsrf_token_rejects_invalid_responses(
    status_code: int,
    text: str,
) -> None:
    """Reject failed responses and pages without an XSRF token."""
    client = Mock()
    client.get.return_value = SimpleNamespace(
        url="https://www.volumeleaders.com/Trades",
        status_code=status_code,
        text=text,
    )

    with pytest.raises(_exceptions.AuthenticationError):
        _auth.fetch_xsrf_token(client, {})
