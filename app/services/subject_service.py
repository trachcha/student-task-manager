from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.subject import Subject
from app.schemas.subject import SubjectCreate, SubjectUpdate


def _get_owned_subject(session: Session, subject_id: int, user_id: int) -> Subject:
    subject = session.get(Subject, subject_id)
    if subject is None or subject.user_id != user_id:
        raise HTTPException(status_code=404, detail="Subject not found")
    return subject


def _ensure_name_available(
    session: Session, user_id: int, name: str, exclude_id: int | None = None
) -> None:
    existing = session.scalars(
        select(Subject).where(Subject.user_id == user_id, Subject.name == name)
    ).first()
    if existing is not None and existing.id != exclude_id:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Subject name already exists",
        )


def create_subject(session: Session, user_id: int, request: SubjectCreate) -> Subject:
    _ensure_name_available(session, user_id, request.name)
    subject = Subject(name=request.name, user_id=user_id)
    session.add(subject)
    session.commit()
    session.refresh(subject)
    return subject


def get_all_subjects(session: Session, user_id: int) -> list[Subject]:
    return list(
        session.scalars(
            select(Subject).where(Subject.user_id == user_id).order_by(Subject.id)
        ).all()
    )


def get_subject_by_id(session: Session, user_id: int, subject_id: int) -> Subject:
    return _get_owned_subject(session, subject_id, user_id)


def update_subject(
    session: Session, user_id: int, subject_id: int, update: SubjectUpdate
) -> Subject:
    subject = _get_owned_subject(session, subject_id, user_id)
    _ensure_name_available(session, user_id, update.name, exclude_id=subject_id)
    subject.name = update.name
    session.commit()
    session.refresh(subject)
    return subject


def delete_subject(session: Session, user_id: int, subject_id: int) -> dict:
    subject = _get_owned_subject(session, subject_id, user_id)
    session.delete(subject)
    session.commit()
    return {"message": "Subject deleted successfully"}
