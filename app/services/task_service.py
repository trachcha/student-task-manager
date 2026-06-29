from fastapi import HTTPException

from app.database.database import get_connection
from app.models.task import Task, TaskRequest, TaskUpdate


def _row_to_task(row: tuple) -> Task:
    return Task(id=row[0], title=row[1], completed=bool(row[2]))


def create_task(request: TaskRequest) -> Task:
    connection = get_connection()
    cursor = connection.cursor()

    insert_task_sql = "INSERT INTO tasks (title, completed) VALUES (?, ?)"
    cursor.execute(insert_task_sql, (request.title, False))

    task_id = cursor.lastrowid

    connection.commit()
    connection.close()

    return Task(id=task_id, title=request.title, completed=False)


def get_all_tasks() -> list[Task]:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("SELECT id, title, completed FROM tasks")
    rows = cursor.fetchall()
    connection.close()

    return [_row_to_task(row) for row in rows]


def find_task_by_id(task_id: int) -> Task:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT id, title, completed FROM tasks WHERE id = ?",
        (task_id,),
    )
    row = cursor.fetchone()
    connection.close()

    if row is None:
        raise HTTPException(status_code=404, detail="Task not found")

    return _row_to_task(row)


def update_task_by_id(task_id: int, update: TaskUpdate) -> Task:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute(
        "UPDATE tasks SET title = ?, completed = ? WHERE id = ?",
        (update.title, update.completed, task_id),
    )

    if cursor.rowcount == 0:
        connection.close()
        raise HTTPException(status_code=404, detail="Task not found")

    connection.commit()
    connection.close()

    return Task(id=task_id, title=update.title, completed=update.completed)


def delete_task_by_id(task_id: int) -> dict:
    connection = get_connection()
    cursor = connection.cursor()

    cursor.execute("DELETE FROM tasks WHERE id = ?", (task_id,))

    if cursor.rowcount == 0:
        connection.close()
        raise HTTPException(status_code=404, detail="Task not found")

    connection.commit()
    connection.close()

    return {"message": "Task deleted successfully"}
