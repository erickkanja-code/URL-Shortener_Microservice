"""Dependencies shared by the API's endpoints."""

from typing import Annotated

from fastapi import Depends
from sqlalchemy.orm import Session

from app.core.database import get_db

SessionDep = Annotated[Session, Depends(get_db)]
"""A database session for the current request. Use as `db: SessionDep`."""