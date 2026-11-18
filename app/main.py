"""Application entry point: creates the FastAPI app and registers the routers.

Run with: uvicorn app.main:app
"""

from fastapi import FastAPI

from app.api import redirect
from app.api.v1.router import api_router

app = FastAPI(title="URL Shortener")

app.include_router(api_router)
app.include_router(redirect.router)