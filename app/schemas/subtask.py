from pydantic import BaseModel, ConfigDict


class SubtaskCreate(BaseModel):
    title: str


class SubtaskUpdate(BaseModel):
    title: str
    completed: bool


class SubtaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    completed: bool = False
    task_id: int
