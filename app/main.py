from fastapi import FastAPI

from models.task import Task
from models.task import TaskRequest

app = FastAPI()

tasks: list[Task] = []
id_counter = 1


@app.get("/")
async def root():
    return {"message": "StudentTask API is running."}


@app.post("/tasks")
def create_task(request: TaskRequest):
    global id_counter

    new_task = Task(
        id=id_counter,
        title=request.title
    )

    id_counter += 1

    tasks.append(new_task)

    return new_task


@app.get("/tasks")
def get_all_tasks():
    return tasks
