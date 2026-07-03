from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.database import get_session
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.task import TaskReorderRequest, TaskRequest, TaskResponse, TaskUpdate
from app.services.task_service import (
    create_task,
    delete_task_by_id,
    find_task_by_id,
    get_all_tasks,
    reorder_tasks,
    update_task_by_id,
)

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create(
    request: TaskRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    return create_task(session, current_user.id, request)


@router.get("", response_model=list[TaskResponse])
def read_all(
    subject_id: int | None = None,
    completed: bool | None = None,
    q: str | None = None,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[TaskResponse]:
    return get_all_tasks(session, current_user.id, subject_id, completed, q)


@router.put("/reorder", response_model=list[TaskResponse])
def reorder(
    request: TaskReorderRequest,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[TaskResponse]:
    return reorder_tasks(
        session,
        current_user.id,
        request.completed,
        request.task_ids,
    )


@router.get("/{task_id}", response_model=TaskResponse)
def read_one(
    task_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    return find_task_by_id(session, current_user.id, task_id)


@router.put("/{task_id}", response_model=TaskResponse)
def update(
    task_id: int,
    request: TaskUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    return update_task_by_id(session, current_user.id, task_id, request)


@router.delete("/{task_id}")
def delete(
    task_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    return delete_task_by_id(session, current_user.id, task_id)
