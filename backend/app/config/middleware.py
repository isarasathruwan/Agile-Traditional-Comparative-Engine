import uuid
import logging

from fastapi import Request
from fastapi.responses import JSONResponse
from jose import JWTError, jwt

from app.config.config import settings
from app.config.request_context import set_request_id

logger = logging.getLogger(__name__)


def _is_whitelisted(path: str) -> bool:
    return any(path == prefix or path.startswith(f"{prefix}/") for prefix in settings.auth_whitelist)


async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    set_request_id(request_id)
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response


async def auth_middleware(request: Request, call_next):
    if request.method == "OPTIONS":
        return await call_next(request)

    if _is_whitelisted(request.url.path):
        return await call_next(request)

    auth_header = request.headers.get("Authorization", "")
    if not auth_header.startswith("Bearer "):
        logger.warning("Authentication rejected method=%s path=%s reason=missing_bearer_token", request.method, request.url.path)
        return JSONResponse(
            status_code=401,
            content={
                "status_code": 401,
                "success": False,
                "message": "Not authenticated.",
                "error_code": "AUTH_401",
                "data": None,
            },
        )
    token = auth_header[7:]
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
        request.state.user_subject = payload.get("sub")
    except JWTError:
        logger.warning("Authentication rejected method=%s path=%s reason=invalid_bearer_token", request.method, request.url.path)
        return JSONResponse(
            status_code=401,
            content={
                "status_code": 401,
                "success": False,
                "message": "Invalid token.",
                "error_code": "AUTH_401",
                "data": None,
            },
        )

    return await call_next(request)
