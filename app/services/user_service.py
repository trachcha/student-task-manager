from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_password, verify_password
from app.models.user import User
from app.schemas.user import UserCreate, UserPreferencesUpdate


def get_user_by_username(session: Session, username: str) -> User | None:
    return session.scalars(select(User).where(User.username == username)).first()


def create_user(session: Session, request: UserCreate) -> User:
    if get_user_by_username(session, request.username) is not None:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Username already registered",
        )

    user = User(
        username=request.username,
        hashed_password=hash_password(request.password),
    )
    session.add(user)
    session.commit()
    session.refresh(user)
    return user


def authenticate_user(session: Session, username: str, password: str) -> User | None:
    user = get_user_by_username(session, username)
    if user is None or not verify_password(password, user.hashed_password):
        return None
    return user


def update_user_preferences(
    session: Session, user_id: int, update: UserPreferencesUpdate
) -> User:
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")
    user.unsorted_label = update.unsorted_label
    session.commit()
    session.refresh(user)
    return user
