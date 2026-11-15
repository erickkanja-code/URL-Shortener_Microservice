import secrets
import string
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel, HttpUrl
from sqlalchemy import select
from sqlalchemy.orm import Session

from ..db import get_db
from ..models import URL, User

router = APIRouter()

ALPHABET = string.ascii_letters + string.digits
SHORT_CODE_LENGTH = 7


class URLCreate(BaseModel):
    url: HttpUrl
    owner_id: int


def generate_short_code(db: Session) -> str:
    while True:
        short_code = "".join(secrets.choice(ALPHABET) for _ in range(SHORT_CODE_LENGTH))
        existing_url = db.scalar(select(URL).where(URL.short_code == short_code))
        if existing_url is None:
            return short_code


@router.post("/", status_code=201)
def create_short_url(payload: URLCreate, db: Annotated[Session, Depends(get_db)]):
    if db.get(User, payload.owner_id) is None:
        raise HTTPException(status_code=404, detail="User not found")

    original_url = str(payload.url)
    existing_url = db.scalar(
        select(URL).where(
            URL.original_url == original_url,
            URL.owner_id == payload.owner_id,
        )
    )
    if existing_url:
        raise HTTPException(status_code=409, detail="This URL has already been shortened")

    short_code = generate_short_code(db)
    new_url = URL(
        original_url=original_url,
        short_code=short_code,
        owner_id=payload.owner_id,
    )
    db.add(new_url)
    db.commit()
    return {"url": short_code}


@router.get("/")
def read_short_url(
    short_url: Annotated[str, Query()], db: Annotated[Session, Depends(get_db)]
):
    url = db.scalar(select(URL).where(URL.short_code == short_url))
    if url is None:
        raise HTTPException(status_code=404, detail="URL not found")
    return RedirectResponse(url=url.original_url, status_code=302)