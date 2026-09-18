import logging

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.exceptions.base_exception import AppException

logger = logging.getLogger(__name__)


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        logger.warning(
            "Request rejected method=%s path=%s status_code=%s error_code=%s reason=%s",
            request.method,
            request.url.path,
            exc.status_code,
            exc.error_code,
            exc.message,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status_code": exc.status_code,
                "success": False,
                "message": exc.message,
                "error_code": exc.error_code,
                "data": None,
            },
        )

    @app.exception_handler(HTTPException)
    async def http_exception_handler(request: Request, exc: HTTPException):
        logger.warning(
            "HTTP request rejected method=%s path=%s status_code=%s reason=%s",
            request.method,
            request.url.path,
            exc.status_code,
            exc.detail,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "status_code": exc.status_code,
                "success": False,
                "message": str(exc.detail),
                "error_code": "HTTP_ERROR",
                "data": None,
            },
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.warning(
            "Request payload validation failed method=%s path=%s details=%s",
            request.method,
            request.url.path,
            exc.errors(),
        )
        return JSONResponse(
            status_code=422,
            content={
                "status_code": 422,
                "success": False,
                "message": "Validation failed.",
                "error_code": "REQ_422",
                "data": {"details": exc.errors()},
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception):
        logger.exception(
            "Unhandled request failure method=%s path=%s exception_type=%s",
            request.method,
            request.url.path,
            type(exc).__name__,
        )
        return JSONResponse(
            status_code=500,
            content={
                "status_code": 500,
                "success": False,
                "message": "Internal server error.",
                "error_code": "SRV_500",
                "data": None,
            },
        )
