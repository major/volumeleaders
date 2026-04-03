"""Tests for authentication helper functions."""

from importlib import import_module
from unittest.mock import Mock

import pytest

_auth = import_module("volumeleaders._auth")
_exceptions = import_module("volumeleaders._exceptions")
extract_cookies = _auth.extract_cookies
fetch_xsrf_token = _auth.fetch_xsrf_token
AuthenticationError = _exceptions.AuthenticationError
CookieExtractionError = _exceptions.CookieExtractionError


def test_extract_cookies_raises_for_unsupported_browser() -> None:
    """Raise CookieExtractionError when browser-cookie3 has no extractor."""
    with pytest.raises(CookieExtractionError):
        extract_cookies("definitely_not_a_real_browser")


def test_fetch_xsrf_token_extracts_hidden_input_value() -> None:
    """Extract XSRF token from authenticated HTML response content."""
    http_client = Mock()
    response = Mock()
    response.url = "https://www.volumeleaders.com/ExecutiveSummary"
    response.status_code = 200
    response.text = (
        '<html><body><input name="__RequestVerificationToken" '
        'type="hidden" value="token-123" /></body></html>'
    )
    http_client.get.return_value = response

    token = fetch_xsrf_token(
        http_client=http_client, cookies={"ASP.NET_SessionId": "x"}
    )

    assert token == "token-123"


def test_fetch_xsrf_token_raises_when_redirected_to_login() -> None:
    """Raise AuthenticationError when the authenticated request redirects."""
    http_client = Mock()
    response = Mock()
    response.url = "https://www.volumeleaders.com/Login"
    response.status_code = 200
    response.text = "<html></html>"
    http_client.get.return_value = response

    with pytest.raises(AuthenticationError):
        fetch_xsrf_token(http_client=http_client, cookies={"ASP.NET_SessionId": "x"})
