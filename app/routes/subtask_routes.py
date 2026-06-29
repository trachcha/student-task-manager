from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.database import get_session
from app.dependencies import get_current_user
from app.models.user import User
from app.schemas.subtask import SubtaskCreate, SubtaskResponse, SubtaskUpdate
from app.services.subtask_service import (
    create_subtask,
    delete_subtask,
    get_all_subtasks,
    get_subtask_by_id,
    update_subtask,
)

router = APIRouter(prefix="/tasks/{task_id}/subtasks", tags=["subtasks"])


@router.post("", response_model=SubtaskResponse, status_code=status.HTTP_201_CREATED)
def create(
    task_id: int,
    request: SubtaskCreate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> SubtaskResponse:
    return create_subtask(session, current_user.id, task_id, request)


@router.get("", response_model=list[SubtaskResponse])
def read_all(
    task_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> list[SubtaskResponse]:
    return get_all_subtasks(session, current_user.id, task_id)


@router.get("/{subtask_id}", response_model=SubtaskResponse)
def read_one(
    task_id: int,
    subtask_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> SubtaskResponse:
    return get_subtask_by_id(session, current_user.id, task_id, subtask_id)


@router.put("/{subtask_id}", response_model=SubtaskResponse)
def update(
    task_id: int,
    subtask_id: int,
    request: SubtaskUpdate,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> SubtaskResponse:
    return update_subtask(session, current_user.id, task_id, subtask_id, request)


@router.delete("/{subtask_id}")
def delete(
    task_id: int,
    subtask_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
) -> dict:
    return delete_subtask(session, current_user.id, task_id, subtask_id)
