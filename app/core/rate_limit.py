"""Rate limiting with SlowAPI.

The limiter counts requests per client IP address. Endpoints opt in with
the `@limiter.limit(...)` decorator. When a client goes over a limit, the
request is answered with 429 Too Many Requests by `rate_limit_exceeded_handler`.
"""

from fastapi import Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.core.config import RATE_LIMIT_STORAGE_URI

limiter = Limiter(key_func=get_remote_address, storage_uri=RATE_LIMIT_STORAGE_URI)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Answer a rate-limited request with 429 and a Retry-After header.

    The body uses the same {"detail": ...} shape as the API's other errors.
    """
    return JSONResponse(
        status_code=429,
        content={"detail": "Too many attempts. Please try again in a minute."},
        headers={"Retry-After": "60"},
    )