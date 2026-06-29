from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.task import Task
from app.schemas.task import TaskRequest, TaskUpdate


def _get_owned_task(session: Session, task_id: int, user_id: int) -> Task:
    task = session.get(Task, task_id)
    if task is None or task.user_id != user_id:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


def create_task(session: Session, user_id: int, request: TaskRequest) -> Task:
    task = Task(title=request.title, completed=False, user_id=user_id)
    session.add(task)
    session.commit()
    session.refresh(task)
    return task


def get_all_tasks(session: Session, user_id: int) -> list[Task]:
    return list(
        session.scalars(
            select(Task).where(Task.user_id == user_id).order_by(Task.id)
        ).all()
    )


def find_task_by_id(session: Session, user_id: int, task_id: int) -> Task:
    return _get_owned_task(session, task_id, user_id)


def update_task_by_id(
    session: Session, user_id: int, task_id: int, update: TaskUpdate
) -> Task:
    task = _get_owned_task(session, task_id, user_id)
    task.title = update.title
    task.completed = update.completed
    session.commit()
    session.refresh(task)
    return task


def delete_task_by_id(session: Session, user_id: int, task_id: int) -> dict:
    task = _get_owned_task(session, task_id, user_id)
    session.delete(task)
    session.commit()
    return {"message": "Task deleted successfully"}
