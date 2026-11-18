"""Collects every version 1 router under the /api/v1 prefix."""

from fastapi import APIRouter

from app.api.v1 import urls

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(urls.router)