from typing import Any, Dict, Optional


class TjfError(Exception):
    """Custom error class for jobs-api errors."""

    http_status_code: int = 500
    data: Dict[str, Any]

    def __init__(
        self,
        message: str,
        *,
        http_status_code: Optional[int] = None,
        data: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(message)

        if http_status_code:
            self.http_status_code = http_status_code

        if data:
            self.data = data
        else:
            self.data = {}


class TjfClientError(TjfError):
    """Custom error class for jobs-api errors caused by the client."""

    http_status_code = 400


class TjfValidationError(TjfClientError):
    """Custom error class for jobs-api errors caused by invalid data."""

    pass
