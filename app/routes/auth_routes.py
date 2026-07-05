from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session

from app.core.limiter import limiter
from app.core.security import create_access_token
from app.database.database import get_session
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.auth import Token
from app.schemas.user import UserCreate, UserPreferencesUpdate, UserResponse
from app.services.user_service import authenticate_user, create_user, update_user_preferences

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit("3/minute")
def register(
    request: Request,
    body: UserCreate,
    session: Session = Depends(get_session),
) -> UserResponse:
    return create_user(session, body)


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session),
) -> Token:
    user = authenticate_user(session, form_data.username, form_data.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return Token(access_token=create_access_token(user.id))


@router.get("/me", response_model=UserResponse)
def read_me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_me(
    request: UserPreferencesUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    return update_user_preferences(session, current_user.id, request)
