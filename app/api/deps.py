"""Dependencies shared by the API's endpoints."""

from typing import Annotated

from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import ACCESS_TOKEN_TYPE, decode_token
from app.models import User

SessionDep = Annotated[Session, Depends(get_db)]
"""A database session for the current request. Use as `db: SessionDep`."""

# Reads the "Authorization: Bearer <token>" header, and adds the Authorize
# button to /docs. auto_error=False lets get_current_user return a consistent
# 401 when the header is missing, instead of HTTPBearer's own error.
bearer_scheme = HTTPBearer(auto_error=False)


def get_current_user(
    db: SessionDep,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
) -> User:
    """Return the user identified by the request's access token.

    Raises 401 if the header is missing, or the token is invalid, expired,
    not an access token, or belongs to a user who no longer exists.
    """
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_id = decode_token(credentials.credentials, expected_type=ACCESS_TOKEN_TYPE)
    user = db.get(User, user_id) if user_id is not None else None

    if user is None:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired access token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]
"""The logged-in user making the request. Use as `current_user: CurrentUserDep`."""