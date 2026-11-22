"""Authentication endpoints, under /api/v1/auth."""

from fastapi import APIRouter

from app.api.deps import SessionDep
from app.schemas.user import UserCreate, UserResponse
from app.services import auth as auth_service

router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register/", status_code=201, response_model=UserResponse)
def register(payload: UserCreate, db: SessionDep):
    """Create a new account. New accounts start on the Free tier."""
    return auth_service.register_user(db, payload)