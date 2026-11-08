from fastapi import Body, APIRouter
from pydantic import BaseModel, HttpUrl
from typing import Annotated
router = APIRouter() # type: ignore

class URL(BaseModel):
    url: HttpUrl



@router.post('/url/') # type: ignore
async def create_short_url(url: Annotated[URL, Body()]):
    return {"url": url}
    