from http import HTTPStatus

from app.exceptions.base_exception import AppException


class UnauthorizedException(AppException):
    def __init__(self, message: str = "Invalid credentials."):
        super().__init__(message=message, status_code=HTTPStatus.UNAUTHORIZED, error_code="AUTH_401")


class ForbiddenException(AppException):
    def __init__(self, message: str = "Permission denied."):
        super().__init__(message=message, status_code=HTTPStatus.FORBIDDEN, error_code="AUTH_403")


class ValidationException(AppException):
    def __init__(self, message: str = "Validation failed."):
        super().__init__(message=message, status_code=HTTPStatus.BAD_REQUEST, error_code="REQ_400")


class ConflictException(AppException):
    def __init__(self, message: str = "Conflict detected."):
        super().__init__(message=message, status_code=HTTPStatus.CONFLICT, error_code="REQ_409")


class NotFoundException(AppException):
    def __init__(self, message: str = "Resource not found."):
        super().__init__(message=message, status_code=HTTPStatus.NOT_FOUND, error_code="RES_404")


class ServiceException(AppException):
    def __init__(self, message: str = "Unable to process request right now."):
        super().__init__(
            message=message,
            status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
            error_code="SRV_500",
        )
