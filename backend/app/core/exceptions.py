from dataclasses import dataclass


@dataclass
class AppError(Exception):
    message: str
    code: str = "app_error"
    status_code: int = 400


class ExternalServiceError(AppError):
    def __init__(self, message: str = "External service call failed"):
        super().__init__(message=message, code="external_service_error", status_code=502)


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(message=message, code="not_found", status_code=404)
