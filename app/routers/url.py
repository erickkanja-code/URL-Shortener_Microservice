from fastapi import Body, APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl
from typing import Annotated, Any
import random
from ..dependency import connect_redis
router = APIRouter()

class URL(BaseModel):
    url: HttpUrl

def shorten_url(long_url: str) -> str:
    domain_begins_at: int = long_url.rfind(".")
    domain_name: str = long_url[domain_begins_at:]
    if long_url.startswith("https://") or long_url.startswith("http://"):
        if long_url.startswith("https://www."):
            website_name_begins_at: int = long_url.find(".")+1
        else:
            website_name_begins_at: int = long_url.find("/")+2
    else:
        website_name_begins_at: int = 0
    short_url: str = long_url[website_name_begins_at: website_name_begins_at+2] + long_url[domain_begins_at-2:domain_begins_at] + str(random.randint(1,9)) + str(random.randint(1,9)) + domain_name[:4]
    return short_url 


@router.post('/') 
async def create_short_url(url: Annotated[URL, Body()], redis_client: Any = Depends(connect_redis)):
    short_url = await redis_client.get(str(url.url))
    if short_url:
        raise HTTPException(status_code=409, detail="This URL has already been shortened")
    short_url = shorten_url(str(url.url))
    await redis_client.set(str(url.url), short_url) 
    await redis_client.set(short_url, str(url.url)) 
    return {"url": short_url} 
    
@router.get('/') 
async def read_short_url(short_url: str = Query(), redis_client: Any = Depends(connect_redis)):
    long_url: str = await redis_client.get(short_url)
    if long_url:
        return RedirectResponse(url=long_url)
    else:
        raise HTTPException(status_code=404, detail="URL not found")


