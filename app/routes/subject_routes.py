from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.database import get_session
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.subject import SubjectCreate, SubjectResponse, SubjectUpdate
from app.services.subject_service import (
    create_subject,
    delete_subject,
    get_all_subjects,
    get_subject_by_id,
    update_subject,
)

router = APIRouter(prefix="/subjects", tags=["subjects"])


@router.post("", response_model=SubjectResponse, status_code=status.HTTP_201_CREATED)
def create(
    request: SubjectCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> SubjectResponse:
    return create_subject(session, current_user.id, request)


@router.get("", response_model=list[SubjectResponse])
def read_all(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[SubjectResponse]:
    return get_all_subjects(session, current_user.id)


@router.get("/{subject_id}", response_model=SubjectResponse)
def read_one(
    subject_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> SubjectResponse:
    return get_subject_by_id(session, current_user.id, subject_id)


@router.put("/{subject_id}", response_model=SubjectResponse)
def update(
    subject_id: int,
    request: SubjectUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> SubjectResponse:
    return update_subject(session, current_user.id, subject_id, request)


@router.delete("/{subject_id}")
def delete(
    subject_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    return delete_subject(session, current_user.id, subject_id)
