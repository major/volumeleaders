"""Thin HTTP client for the VolumeLeaders API.

Manages auth state (cookies + XSRF token) and provides base request
methods that endpoint modules build on.
"""

from typing import Any

import httpx

from volumeleaders._auth import BASE_URL, USER_AGENT, extract_cookies, fetch_xsrf_token
from volumeleaders._exceptions import APIError


class VolumeLeadersClient:
    """Client for the VolumeLeaders API.

    Extracts auth cookies from the user's browser and fetches the XSRF
    token on initialization. All API methods delegate to endpoint modules.

    Args:
        browser: Browser to extract cookies from (default: "firefox").
        timeout: HTTP request timeout in seconds (default: 30.0).
    """

    def __init__(self, browser: str = "firefox", timeout: float = 60.0) -> None:
        """Initialize the client with browser cookies and XSRF token."""
        self._http = httpx.Client(
            base_url=BASE_URL,
            timeout=timeout,
            headers={"User-Agent": USER_AGENT},
        )
        self._cookies = extract_cookies(browser)
        self._xsrf_token = fetch_xsrf_token(self._http, self._cookies)

    def close(self) -> None:
        """Close the underlying HTTP client."""
        self._http.close()

    def __enter__(self) -> "VolumeLeadersClient":
        """Support use as a context manager."""
        return self

    def __exit__(self, *args: object) -> None:
        """Close the client on context manager exit."""
        self.close()

    def _request_headers(self) -> dict[str, str]:
        """Build the common headers required for all API requests."""
        return {
            "x-xsrf-token": self._xsrf_token,
            "x-requested-with": "XMLHttpRequest",
            "Accept": "application/json, text/javascript, */*; q=0.01",
        }

    def _post(
        self,
        path: str,
        *,
        json: dict[str, Any] | None = None,
        content: str | None = None,
    ) -> Any:
        """Send a POST request and return parsed JSON.

        Centralizes error wrapping and status code validation for all
        API request methods.

        Args:
            path: API path relative to base URL.
            json: JSON-serializable body (mutually exclusive with content).
            content: Pre-encoded string body (mutually exclusive with json).

        Raises:
            APIError: On non-200 response or request failure.

        Returns:
            Parsed JSON response.
        """
        headers = {**self._request_headers()}
        if content is not None:
            headers["Content-Type"] = "application/x-www-form-urlencoded; charset=UTF-8"
        else:
            headers["Content-Type"] = "application/json"

        try:
            resp = self._http.post(
                path,
                json=json,
                content=content,
                headers=headers,
                cookies=self._cookies,
            )
        except httpx.HTTPError as exc:
            raise APIError(f"Request to {path} failed: {exc}") from exc

        if resp.status_code != 200:
            raise APIError(
                f"{path} returned HTTP {resp.status_code}: {resp.text[:200]}",
                status_code=resp.status_code,
            )

        return resp.json()

    def post_json(self, path: str, payload: dict[str, Any]) -> Any:
        """POST a JSON body and return the parsed response.

        Used by simple JSON endpoints like GetExhaustionScores, GetCompany,
        GetSnapshot, and GetAllPriceVolumeTradeData.

        Args:
            path: API path (e.g. "/ExecutiveSummary/GetExhaustionScores").
            payload: JSON-serializable request body.

        Raises:
            APIError: On non-200 response or request failure.

        Returns:
            Parsed JSON response (dict, list, or string depending on endpoint).
        """
        return self._post(path, json=payload)

    def post_datatables(self, path: str, body: str) -> list[dict[str, Any]]:
        """POST a DataTables form-encoded body and return the data array.

        Handles the DataTables response wrapper, extracting the "data" array.

        Args:
            path: API path (e.g. "/Trades/GetTrades").
            body: URL-encoded form body from DataTablesRequest.encode().

        Raises:
            APIError: On non-200 response, request failure, or missing "data" key.

        Returns:
            List of row dicts from the "data" array in the response.
        """
        result = self._post(path, content=body)
        if isinstance(result, dict) and "data" in result:
            return result["data"]

        raise APIError(f"Unexpected response format from {path}: missing 'data' key")

    def post_datatables_raw(self, path: str, body: str) -> dict[str, Any]:
        """POST a DataTables form-encoded body and return the full response.

        Like post_datatables but returns the complete response including
        recordsTotal and recordsFiltered for pagination.

        Args:
            path: API path.
            body: URL-encoded form body.

        Raises:
            APIError: On non-200 response or request failure.

        Returns:
            Full response dict with "data", "recordsTotal", "recordsFiltered".
        """
        return self._post(path, content=body)
