from fastapi import FastAPI

from .routers.url import redirect_router, router as url_router

app = FastAPI(title="URL Shortener")

app.include_router(url_router)
app.include_router(redirect_router)