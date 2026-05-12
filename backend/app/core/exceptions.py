
class AppException(Exception):
    def __init__(self, status_code: int, error: str, detail: str, retryable: bool = False):
        self.status_code = status_code
        self.error = error
        self.detail = detail
        self.retryable = retryable


class NotFoundException(AppException):
    def __init__(self, detail: str = "Resource not found"):
        super().__init__(404, "NOT_FOUND", detail)


class ConflictException(AppException):
    def __init__(self, detail: str = "State conflict"):
        super().__init__(409, "CONFLICT", detail)


class ValidationException(AppException):
    def __init__(self, detail: str = "Validation error", field_errors: dict | None = None):
        super().__init__(422, "VALIDATION_ERROR", detail)
        self.field_errors = field_errors or {}


class UpstreamServiceException(AppException):
    def __init__(self, detail: str = "Upstream service error"):
        super().__init__(502, "UPSTREAM_ERROR", detail, retryable=True)
