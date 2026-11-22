"""Authentication endpoints, under /api/v1/auth."""

from fastapi import APIRouter, Request

from app.api.deps import SessionDep
from app.core.config import LOGIN_RATE_LIMIT
from app.core.rate_limit import limiter
from app.schemas.auth import AccessToken, LoginRequest, RefreshRequest, TokenPair
from app.schemas.user import UserCreate, UserResponse
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register/", status_code=201, response_model=UserResponse)
def register(payload: UserCreate, db: SessionDep):
    """Create a new account. New accounts start on the Free tier."""
    return auth_service.register_user(db, payload)


@router.post("/login/", response_model=TokenPair)
@limiter.limit(LOGIN_RATE_LIMIT)
def login(request: Request, payload: LoginRequest, db: SessionDep):
    """Log in with email and password, and receive an access and a refresh token.

    Limited to 5 attempts per minute per IP address, to slow down password
    guessing. Further attempts get 429 Too Many Requests.
    """
    return auth_service.login(db, payload)


@router.post("/refresh/", response_model=AccessToken)
def refresh(payload: RefreshRequest, db: SessionDep):
    """Exchange a refresh token for a new access token."""
    return auth_service.refresh_access_token(db, payload.refresh_token)