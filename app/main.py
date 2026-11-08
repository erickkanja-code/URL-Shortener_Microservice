from fastapi import FastAPI
from .routers.url import router # type: ignore
app = FastAPI()

app.include_router(router) # type: ignore



