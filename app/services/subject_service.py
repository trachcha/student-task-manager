from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.subject import Subject
from app.models.user import User
from app.schemas.subject import SubjectCreate, SubjectUpdate

UNSORTED_SUBJECT_ID = 0


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


def _next_position(session: Session, user_id: int) -> int:
    max_position = session.scalar(
        select(func.coalesce(func.max(Subject.position), -1)).where(
            Subject.user_id == user_id
        )
    )
    return max_position + 1


def create_subject(session: Session, user_id: int, request: SubjectCreate) -> Subject:
    _ensure_name_available(session, user_id, request.name)
    subject = Subject(
        name=request.name,
        position=_next_position(session, user_id),
        user_id=user_id,
    )
    session.add(subject)
    session.commit()
    session.refresh(subject)
    return subject


def get_all_subjects(session: Session, user_id: int) -> list[Subject]:
    return list(
        session.scalars(
            select(Subject)
            .where(Subject.user_id == user_id)
            .order_by(Subject.position, Subject.id)
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


def reorder_subjects(
    session: Session, user_id: int, subject_ids: list[int]
) -> list[Subject]:
    user = session.get(User, user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="User not found")

    owned_subjects = list(
        session.scalars(select(Subject).where(Subject.user_id == user_id)).all()
    )
    owned_ids = {subject.id for subject in owned_subjects}
    expected_ids = owned_ids | {UNSORTED_SUBJECT_ID}

    if set(subject_ids) != expected_ids:
        raise HTTPException(status_code=400, detail="Invalid subject order")
    if subject_ids.count(UNSORTED_SUBJECT_ID) != 1:
        raise HTTPException(status_code=400, detail="Invalid subject order")

    subject_map = {subject.id: subject for subject in owned_subjects}
    real_position = 0
    for index, subject_id in enumerate(subject_ids):
        if subject_id == UNSORTED_SUBJECT_ID:
            user.unsorted_position = index
        else:
            subject_map[subject_id].position = real_position
            real_position += 1

    session.commit()
    return get_all_subjects(session, user_id)


def delete_subject(session: Session, user_id: int, subject_id: int) -> dict:
    subject = _get_owned_subject(session, subject_id, user_id)
    session.delete(subject)
    session.commit()
    return {"message": "Subject deleted successfully"}
