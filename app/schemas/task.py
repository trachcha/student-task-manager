from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_core import PydanticCustomError

TaskPriority = Literal["low", "medium", "high"]
VALID_PRIORITIES = {"low", "medium", "high"}


def _validate_task_title_length(value: str) -> str:
    if len(value) > 200:
        raise PydanticCustomError(
            "title_too_long",
            "Task titles must be under 200 characters",
        )
    return value


def _validate_description_length(value: str | None) -> str | None:
    if value is not None and len(value) > 2000:
        raise PydanticCustomError(
            "description_too_long",
            "Task descriptions must be under 2000 characters",
        )
    return value


class TaskRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1)
    description: str | None = None
    priority: TaskPriority = "medium"
    due_date: date | None = None
    subject_id: int | None = None

    @field_validator("title")
    @classmethod
    def validate_title_length(cls, value: str) -> str:
        return _validate_task_title_length(value)

    @field_validator("description")
    @classmethod
    def validate_description_length(cls, value: str | None) -> str | None:
        return _validate_description_length(value)


class TaskUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1)
    description: str | None = None
    priority: TaskPriority = "medium"
    due_date: date | None = None
    completed: bool
    subject_id: int | None = None

    @field_validator("title")
    @classmethod
    def validate_title_length(cls, value: str) -> str:
        return _validate_task_title_length(value)

    @field_validator("description")
    @classmethod
    def validate_description_length(cls, value: str | None) -> str | None:
        return _validate_description_length(value)


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None = None
    priority: TaskPriority = "medium"
    due_date: date | None = None
    completed: bool = False
    position: int = 0
    subject_id: int | None = None


class TaskReorderRequest(BaseModel):
    completed: bool
    task_ids: list[int] = Field(min_length=1)
