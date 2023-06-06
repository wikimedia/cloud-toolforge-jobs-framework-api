from typing import Any, Dict, Optional
from toolforge_weld.errors import ToolforgeError, ToolforgeUserError


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


def tjf_error_from_weld_error(error: ToolforgeError) -> TjfError:
    error_class = TjfError
    if isinstance(error, ToolforgeUserError):
        error_class = TjfClientError

    return error_class(message=error.message, data=error.context)
