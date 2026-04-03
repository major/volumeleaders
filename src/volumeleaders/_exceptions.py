"""Custom exceptions for the VolumeLeaders client."""


class VolumeLeadersError(Exception):
    """Base exception for all VolumeLeaders errors."""


class CookieExtractionError(VolumeLeadersError):
    """Failed to extract cookies from the browser.

    Raised when browser-cookie3 cannot read cookies, typically because
    the browser is not installed or the user is not logged in.
    """

    def __init__(self, message: str, *, browser: str) -> None:
        super().__init__(message)
        self.browser = browser


class AuthenticationError(VolumeLeadersError):
    """Authentication with VolumeLeaders failed.

    Raised when the XSRF token cannot be extracted from the page,
    or when the server redirects to the login page (session expired).
    """


class APIError(VolumeLeadersError):
    """An API request to VolumeLeaders failed.

    Raised on non-200 responses or unexpected response formats.
    """

    def __init__(self, message: str, *, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code
