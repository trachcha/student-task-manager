from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.subtask import Subtask
from app.schemas.subtask import SubtaskCreate, SubtaskUpdate
from app.services.task_service import find_task_by_id


def _get_owned_subtask(
    session: Session, user_id: int, task_id: int, subtask_id: int
) -> Subtask:
    find_task_by_id(session, user_id, task_id)
    subtask = session.get(Subtask, subtask_id)
    if subtask is None or subtask.task_id != task_id:
        raise HTTPException(status_code=404, detail="Subtask not found")
    return subtask


def create_subtask(
    session: Session, user_id: int, task_id: int, request: SubtaskCreate
) -> Subtask:
    find_task_by_id(session, user_id, task_id)
    subtask = Subtask(title=request.title, completed=False, task_id=task_id)
    session.add(subtask)
    session.commit()
    session.refresh(subtask)
    return subtask


def get_all_subtasks(session: Session, user_id: int, task_id: int) -> list[Subtask]:
    find_task_by_id(session, user_id, task_id)
    return list(
        session.scalars(
            select(Subtask).where(Subtask.task_id == task_id).order_by(Subtask.id)
        ).all()
    )


def get_subtask_by_id(
    session: Session, user_id: int, task_id: int, subtask_id: int
) -> Subtask:
    return _get_owned_subtask(session, user_id, task_id, subtask_id)


def update_subtask(
    session: Session,
    user_id: int,
    task_id: int,
    subtask_id: int,
    update: SubtaskUpdate,
) -> Subtask:
    subtask = _get_owned_subtask(session, user_id, task_id, subtask_id)
    subtask.title = update.title
    subtask.completed = update.completed
    session.commit()
    session.refresh(subtask)
    return subtask


def delete_subtask(
    session: Session, user_id: int, task_id: int, subtask_id: int
) -> dict:
    subtask = _get_owned_subtask(session, user_id, task_id, subtask_id)
    session.delete(subtask)
    session.commit()
    return {"message": "Subtask deleted successfully"}
