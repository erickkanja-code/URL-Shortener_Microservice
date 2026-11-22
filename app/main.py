"""Application entry point: creates the FastAPI app and registers the routers.

Run with: uvicorn app.main:app
"""

from fastapi import FastAPI
from slowapi.errors import RateLimitExceeded

from app.api import redirect
from app.api.v1.router import api_router
from app.core.rate_limit import limiter, rate_limit_exceeded_handler

app = FastAPI(title="URL Shortener")

# SlowAPI finds the limiter on app.state, and the handler turns
# RateLimitExceeded errors into 429 responses.
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)

app.include_router(api_router)
app.include_router(redirect.router)