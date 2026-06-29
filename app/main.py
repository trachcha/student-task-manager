from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.database.database import initialize_db
from app.routes.auth_routes import router as auth_router
from app.routes.subject_routes import router as subject_router
from app.routes.subtask_routes import router as subtask_router
from app.routes.task_routes import router as task_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    initialize_db()
    yield


app = FastAPI(title="Student Task API", lifespan=lifespan)

app.include_router(auth_router)
app.include_router(subject_router)
app.include_router(task_router)
app.include_router(subtask_router)


@app.get("/", tags=["health"])
def root():
    return {"message": "StudentTask API is running"}
