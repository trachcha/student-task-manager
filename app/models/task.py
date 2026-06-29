from pydantic import BaseModel


class TaskRequest(BaseModel):
    title: str


class TaskUpdate(BaseModel):
    title: str
    completed: bool


class Task(BaseModel):
    id: int
    title: str
    completed: bool = False
