from fastapi import FastAPI

from app.database.database import initialize_db
from app.models.task import TaskRequest, TaskUpdate
from app.services.task_service import (
    create_task,
    get_all_tasks,
    find_task_by_id,
    update_task_by_id,
    delete_task_by_id
)
app = FastAPI()
initialize_db()


@app.get("/")
async def root():
    return {"message": "StudentTask API is running"}


@app.post("/tasks")
def create(request: TaskRequest):
    return create_task(request)


@app.get("/tasks")
def read_all():
    return get_all_tasks()


@app.get("/tasks/{task_id}")
def read_one(task_id: int):
    return find_task_by_id(task_id)


@app.put("/tasks/{task_id}")
def update(task_id: int, request: TaskUpdate):
    return update_task_by_id(task_id, request)


@app.delete("/tasks/{task_id}")
def delete(task_id: int):
    return delete_task_by_id(task_id)
