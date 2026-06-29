# Student Task API

A simple task-management REST API built with FastAPI and SQLite, created to learn backend fundamentals and professional software engineering practices.

The project follows a layered architecture where HTTP routes delegate to a service layer, which is the single point of access to the SQLite database.

```
Routes (main.py) -> Services (task_service.py) -> SQLite (tasks.db)
```

## Tech Stack

- Python 3.12
- FastAPI
- SQLite (via the standard library `sqlite3`, raw SQL)
- Uvicorn (ASGI server)

## Project Structure

```
student-task-api/
├── app/
│   ├── database/
│   │   └── database.py        # Connection + schema initialization
│   ├── models/
│   │   └── task.py            # Pydantic request/response models
│   ├── routes/               # (reserved for future route modules)
│   ├── services/
│   │   └── task_service.py    # Business logic + SQL queries
│   └── main.py                # FastAPI app and route definitions
├── requirements.txt
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.12+

### Setup

```bash
# Clone the repository
git clone <repository-url>
cd student-task-api

# Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### Running the API

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`.

The SQLite database file (`tasks.db`) is created automatically on startup if it does not already exist.

### Interactive Documentation

FastAPI generates interactive API docs automatically:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## API Endpoints

| Method | Path               | Description            | Request Body                         | Success Response          |
|--------|--------------------|------------------------|--------------------------------------|---------------------------|
| GET    | `/`                | Health check           | -                                    | `200` status message      |
| POST   | `/tasks`           | Create a task          | `{ "title": "string" }`              | `200` created task        |
| GET    | `/tasks`           | List all tasks         | -                                    | `200` array of tasks      |
| GET    | `/tasks/{task_id}` | Get a single task      | -                                    | `200` task / `404`        |
| PUT    | `/tasks/{task_id}` | Update a task          | `{ "title": "string", "completed": bool }` | `200` updated task / `404` |
| DELETE | `/tasks/{task_id}` | Delete a task          | -                                    | `200` message / `404`     |

### Data Model

A task is represented as:

```json
{
  "id": 1,
  "title": "Study SQL",
  "completed": false
}
```

### Example Requests

```bash
# Create a task
curl -X POST http://127.0.0.1:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Study SQL"}'

# List all tasks
curl http://127.0.0.1:8000/tasks

# Update a task
curl -X PUT http://127.0.0.1:8000/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"title": "Study SQL", "completed": true}'

# Delete a task
curl -X DELETE http://127.0.0.1:8000/tasks/1
```

## Roadmap

- [x] CRUD operations with in-memory storage
- [x] Service layer architecture
- [x] SQLite-backed persistence with raw SQL
- [ ] Extract routes into dedicated route modules
- [ ] Migrate to PostgreSQL with environment-based configuration
- [ ] Introduce SQLAlchemy ORM and migrations
- [ ] Containerization and cloud deployment

## Contributing

This project uses the [Conventional Commits](https://www.conventionalcommits.org/) specification for commit messages, for example:

```
feat(tasks): add task completion filtering
fix(database): close connection on error paths
docs: document API endpoints in README
```
