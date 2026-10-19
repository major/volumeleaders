"""Authentication helpers for the VolumeLeaders client.

Extracts cookies from the user's browser via browser-cookie3 and retrieves
the XSRF token from the page HTML.
"""

import re
from datetime import UTC, datetime
from http import HTTPStatus
from typing import TYPE_CHECKING

import browser_cookie3

from volumeleaders._exceptions import AuthenticationError, CookieExtractionError

if TYPE_CHECKING:
    import httpx

BASE_URL = "https://www.volumeleaders.com"
USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:149.0) Gecko/20100101 Firefox/149.0"
)

# Matches the hidden input's value attribute for the XSRF token.
_XSRF_RE = re.compile(
    r'<input\s+name="__RequestVerificationToken"\s+type="hidden"\s+value="([^"]+)"',
)


def extract_cookies(browser: str = "firefox") -> dict[str, str]:
    """Extract VolumeLeaders auth cookies from the user's browser.

    The user must be logged in to volumeleaders.com in the specified browser.

    Args:
        browser: Browser name supported by browser-cookie3 (e.g. "firefox", "chrome").

    Raises:
        CookieExtractionError: If cookie extraction fails or required cookies
            are missing.

    Returns:
        Dict of cookie name -> value for the required auth cookies. Currently
        includes ``.ASPXAUTH``, ``ASP.NET_SessionId``, ``VLDeviceID``, and
        ``__RequestVerificationToken``. ``VLDeviceID`` was added upstream in
        late 2026 and is required for the server to honor the session.

    """
    try:
        extractor = getattr(browser_cookie3, browser)
    except AttributeError:
        msg = f"Browser {browser!r} is not supported by browser-cookie3"
        raise CookieExtractionError(msg, browser=browser) from None

    try:
        cj = extractor(domain_name=".volumeleaders.com")
    except Exception as exc:
        msg = f"Failed to extract cookies from {browser!r}: {exc}"
        raise CookieExtractionError(
            msg,
            browser=browser,
        ) from exc

    cookies: dict[str, str] = {}
    for cookie in cj:
        if cookie.name in (
            "__RequestVerificationToken",
            "ASP.NET_SessionId",
            "VLDeviceID",
            ".ASPXAUTH",
        ):
            cookies[cookie.name] = cookie.value

    required = {"ASP.NET_SessionId", ".ASPXAUTH", "VLDeviceID"}
    missing = required - cookies.keys()
    if missing:
        msg = (
            f"Missing required cookies: {sorted(missing)}. "
            f"Are you logged in to volumeleaders.com in {browser}?"
        )
        raise CookieExtractionError(
            msg,
            browser=browser,
        )

    return cookies


def fetch_xsrf_token(
    http_client: httpx.Client,
    cookies: dict[str, str],
) -> str:
    """Fetch the XSRF token by loading an authenticated page.

    Makes a GET request to the Trades page and extracts the hidden
    ``__RequestVerificationToken`` input value from the HTML. Trades is
    used because it returns 200 for an authorized session while still
    embedding the XSRF token; upstream switched away from the legacy
    ``/ExecutiveSummary`` endpoint which now redirects to a separate
    Azure-hosted login page.

    The minimum required query parameters are ``StartDate`` and
    ``EndDate`` (any date works for the auth probe). ``Tickers`` is left
    empty so the server returns no rows but still issues a token.

    Args:
        http_client: Configured httpx client.
        cookies: Auth cookies from extract_cookies().

    Raises:
        AuthenticationError: If the page redirects to login or the token
            cannot be found in the HTML.

    Returns:
        The XSRF token string for use in the x-xsrf-token header.

    """
    today = datetime.now(tz=UTC).date().isoformat()
    resp = http_client.get(
        f"{BASE_URL}/Trades",
        params={"Tickers": "", "StartDate": today, "EndDate": today},
        cookies=cookies,
        follow_redirects=False,
    )

    if "/Login" in str(resp.url):
        msg = (
            "Session expired: redirected to login page. "
            "Log in to volumeleaders.com in your browser and try again."
        )
        raise AuthenticationError(msg)

    if resp.status_code != HTTPStatus.OK:
        msg = f"Failed to load page for XSRF token: HTTP {resp.status_code}"
        raise AuthenticationError(
            msg,
        )

    match = _XSRF_RE.search(resp.text)
    if not match:
        msg = (
            "Could not find __RequestVerificationToken in page HTML. "
            "The page structure may have changed."
        )
        raise AuthenticationError(
            msg,
        )

    return match.group(1)
