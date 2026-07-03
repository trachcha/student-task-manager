from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.subject import Subject
from app.models.task import Task
from app.schemas.task import TaskRequest, TaskUpdate


def _get_owned_task(session: Session, task_id: int, user_id: int) -> Task:
    task = session.get(Task, task_id)
    if task is None or task.user_id != user_id:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


def _validate_subject(session: Session, user_id: int, subject_id: int | None) -> None:
    if subject_id is None:
        return
    subject = session.get(Subject, subject_id)
    if subject is None or subject.user_id != user_id:
        raise HTTPException(status_code=404, detail="Subject not found")


def _escape_like(value: str) -> str:
    """Escape LIKE/ILIKE wildcards so they are matched literally."""
    return value.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_")


def _next_position(session: Session, user_id: int, completed: bool) -> int:
    max_position = session.scalar(
        select(func.coalesce(func.max(Task.position), -1)).where(
            Task.user_id == user_id,
            Task.completed == completed,
        )
    )
    return max_position + 1


def create_task(session: Session, user_id: int, request: TaskRequest) -> Task:
    _validate_subject(session, user_id, request.subject_id)
    task = Task(
        title=request.title,
        completed=False,
        position=_next_position(session, user_id, False),
        user_id=user_id,
        subject_id=request.subject_id,
    )
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def get_all_tasks(
    session: Session,
    user_id: int,
    subject_id: int | None = None,
    completed: bool | None = None,
    q: str | None = None,
) -> list[Task]:
    query = select(Task).where(Task.user_id == user_id)
    if subject_id is not None:
        query = query.where(Task.subject_id == subject_id)
    if completed is not None:
        query = query.where(Task.completed == completed)
    if q and q.strip():
        pattern = "%" + _escape_like(q.strip()) + "%"
        query = query.where(Task.title.ilike(pattern, escape="\\"))
    return list(session.scalars(query.order_by(Task.position, Task.id)).all())


def find_task_by_id(session: Session, user_id: int, task_id: int) -> Task:
    return _get_owned_task(session, task_id, user_id)


def update_task_by_id(
    session: Session, user_id: int, task_id: int, update: TaskUpdate
) -> Task:
    task = _get_owned_task(session, task_id, user_id)
    _validate_subject(session, user_id, update.subject_id)
    was_completed = task.completed
    task.title = update.title
    task.completed = update.completed
    task.subject_id = update.subject_id
    if was_completed != update.completed:
        task.position = _next_position(session, user_id, update.completed)
    if update.completed:
        for subtask in task.subtasks:
            subtask.completed = True
    session.commit()
    session.refresh(task)
    return task


def reorder_tasks(
    session: Session,
    user_id: int,
    completed: bool,
    task_ids: list[int],
) -> list[Task]:
    bucket_tasks = list(
        session.scalars(
            select(Task).where(Task.user_id == user_id, Task.completed == completed)
        ).all()
    )
    bucket_ids = {task.id for task in bucket_tasks}
    if set(task_ids) != bucket_ids:
        raise HTTPException(status_code=400, detail="Invalid task order")

    task_map = {task.id: task for task in bucket_tasks}
    for position, task_id in enumerate(task_ids):
        task_map[task_id].position = position

    session.commit()
    return get_all_tasks(session, user_id, completed=completed)


def delete_task_by_id(session: Session, user_id: int, task_id: int) -> dict:
    task = _get_owned_task(session, task_id, user_id)
    session.delete(task)
    session.commit()
    return {"message": "Task deleted successfully"}
