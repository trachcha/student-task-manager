from pydantic import BaseModel, ConfigDict


class TaskRequest(BaseModel):
    title: str
    subject_id: int | None = None


class TaskUpdate(BaseModel):
    title: str
    completed: bool
    subject_id: int | None = None


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    completed: bool = False
    subject_id: int | None = None
