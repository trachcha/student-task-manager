from pydantic import BaseModel, ConfigDict, Field, field_validator
from pydantic_core import PydanticCustomError


def _validate_task_title_length(value: str) -> str:
    if len(value) > 200:
        raise PydanticCustomError(
            "title_too_long",
            "Task titles must be under 200 characters",
        )
    return value


class TaskRequest(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1)
    subject_id: int | None = None

    @field_validator("title")
    @classmethod
    def validate_title_length(cls, value: str) -> str:
        return _validate_task_title_length(value)


class TaskUpdate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(min_length=1)
    completed: bool
    subject_id: int | None = None

    @field_validator("title")
    @classmethod
    def validate_title_length(cls, value: str) -> str:
        return _validate_task_title_length(value)


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    completed: bool = False
    position: int = 0
    subject_id: int | None = None


class TaskReorderRequest(BaseModel):
    completed: bool
    task_ids: list[int] = Field(min_length=1)
