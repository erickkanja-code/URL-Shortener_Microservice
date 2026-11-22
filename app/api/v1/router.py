"""Collects every version 1 router under the /api/v1 prefix."""

from fastapi import APIRouter

from app.api.v1 import analytics, auth, urls

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(auth.router)
api_router.include_router(urls.router)
api_router.include_router(analytics.router)