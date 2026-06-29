# Student Task API

A simple task-management REST API built with FastAPI and PostgreSQL, created to learn backend fundamentals and professional software engineering practices.

The project follows a layered architecture where HTTP routes delegate to a service layer, which is the single point of access to the database. Tasks are owned by authenticated users.

```
Routes (task_routes.py) -> Services (task_service.py) -> SQLAlchemy Session -> PostgreSQL
```

## Tech Stack

- Python 3.12
- FastAPI
- SQLAlchemy 2.0 (typed ORM) on PostgreSQL via the `postgresql+psycopg://` (psycopg 3) dialect
- Alembic (database migrations)
- JWT bearer authentication (PyJWT) with bcrypt password hashing (pwdlib)
- Docker / Docker Compose (local database)
- Uvicorn (ASGI server)
- pytest (automated tests)

## Project Structure

```
student-task-api/
├── app/
│   ├── core/
│   │   ├── config.py          # Settings (JWT secret, token expiry)
│   │   └── security.py        # Password hashing + JWT helpers
│   ├── database/
│   │   └── database.py        # Engine, session factory, Base, get_session
│   ├── models/
│   │   ├── subject.py         # Subject ORM model (owned by a user)
│   │   ├── subtask.py         # Subtask ORM model (belongs to a task)
│   │   ├── task.py            # Task ORM model (owned by a user)
│   │   └── user.py            # User ORM model
│   ├── schemas/
│   │   ├── auth.py            # Token schema
│   │   ├── subject.py         # Subject request/response schemas
│   │   ├── subtask.py         # Subtask request/response schemas
│   │   ├── task.py            # Task request/response schemas
│   │   └── user.py            # User request/response schemas
│   ├── routes/
│   │   ├── auth_routes.py     # Register / login / me endpoints
│   │   ├── subject_routes.py  # APIRouter with subject endpoints
│   │   ├── subtask_routes.py  # APIRouter with nested subtask endpoints
│   │   └── task_routes.py     # APIRouter with task endpoints
│   ├── services/
│   │   ├── subject_service.py # Owner-scoped subject operations
│   │   ├── subtask_service.py # Subtask operations (scoped via parent task)
│   │   ├── task_service.py    # Owner-scoped task operations
│   │   └── user_service.py    # User creation + authentication
│   ├── dependencies.py        # OAuth2 scheme + get_current_user
│   └── main.py                # FastAPI app: wiring and router registration
├── alembic/
│   ├── env.py                 # Migration environment (reads DATABASE_URL)
│   └── versions/              # Migration scripts
├── alembic.ini                # Alembic configuration
├── db/
│   └── init/                  # SQL run on first DB container start
├── tests/
│   ├── conftest.py            # Shared fixtures (isolated test database)
│   ├── test_auth.py           # Auth + ownership tests
│   ├── test_subjects.py       # Subject endpoint tests
│   ├── test_subtasks.py       # Subtask endpoint tests
│   └── test_tasks.py          # Task endpoint tests
├── docker-compose.yml         # Local PostgreSQL service
├── .env.example
├── pytest.ini
├── requirements.txt
└── README.md
```

## Getting Started

### Prerequisites

- Python 3.12+
- Docker and Docker Compose (for the local PostgreSQL database)

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

# Copy the example environment file
cp .env.example .env
```

### Start PostgreSQL

The project ships with a Docker Compose file that runs PostgreSQL 16 and, on
first start, creates a separate database used by the test suite.

```bash
docker compose up -d
```

This exposes PostgreSQL on `localhost:5432` with two databases:

- `student_tasks` — used by the application
- `student_tasks_test` — used by the automated tests

To stop it (data is preserved in a named volume):

```bash
docker compose down
```

### Running the API

```bash
uvicorn app.main:app --reload
```

The API will be available at `http://127.0.0.1:8000`. For local convenience the
`tasks` table is created automatically on startup if it does not already exist;
the canonical way to manage the schema is Alembic migrations (see below).

### Configuration

Configuration is read from environment variables (a local `.env` file is loaded
automatically). See [.env.example](.env.example).

| Variable            | Default                                                       | Description                                       |
|---------------------|---------------------------------------------------------------|---------------------------------------------------|
| `DATABASE_URL`      | `postgresql://postgres:postgres@localhost:5432/student_tasks` | Connection string for the application database.   |
| `TEST_DATABASE_URL` | `postgresql://postgres:postgres@localhost:5432/student_tasks_test` | Connection string used by the test suite.    |
| `SECRET_KEY`        | `dev-secret-change-me`                                         | Secret used to sign JWTs. Override in every real environment. |
| `ALGORITHM`         | `HS256`                                                       | JWT signing algorithm.                            |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30`                                               | Access token lifetime in minutes.                 |

### Interactive Documentation

FastAPI generates interactive API docs automatically:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Authentication

The API uses JWT bearer authentication. Register an account, log in to obtain an
access token, and send it as an `Authorization: Bearer <token>` header on every
task request. All `/tasks` endpoints are private: each user only sees and manages
their own tasks (requests for another user's task return `404`).

```bash
# 1. Register
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "student@example.com", "password": "password123"}'

# 2. Log in (form-encoded; the OAuth2 "username" field carries the email)
curl -X POST http://127.0.0.1:8000/auth/login \
  -d "username=student@example.com&password=password123"
# -> { "access_token": "<JWT>", "token_type": "bearer" }

# 3. Call a protected endpoint
curl http://127.0.0.1:8000/tasks \
  -H "Authorization: Bearer <JWT>"
```

In Swagger UI (`/docs`) use the **Authorize** button and log in with the email as
the username to try the protected endpoints interactively.

## API Endpoints

| Method | Path               | Auth   | Description            | Request Body                         | Success Response          |
|--------|--------------------|--------|------------------------|--------------------------------------|---------------------------|
| GET    | `/`                | No     | Health check           | -                                    | `200` status message      |
| POST   | `/auth/register`   | No     | Create an account      | `{ "email": "string", "password": "string" }` | `201` created user / `409` |
| POST   | `/auth/login`      | No     | Obtain an access token | form: `username` (email), `password` | `200` token / `401`       |
| GET    | `/auth/me`         | Yes    | Current user           | -                                    | `200` user                |
| POST   | `/subjects`        | Yes    | Create a subject       | `{ "name": "string" }`               | `201` created subject / `409` |
| GET    | `/subjects`        | Yes    | List your subjects     | -                                    | `200` array of subjects   |
| GET    | `/subjects/{id}`   | Yes    | Get one of your subjects | -                                  | `200` subject / `404`     |
| PUT    | `/subjects/{id}`   | Yes    | Rename your subject    | `{ "name": "string" }`               | `200` updated subject / `404` / `409` |
| DELETE | `/subjects/{id}`   | Yes    | Delete your subject    | -                                    | `200` message / `404`     |
| POST   | `/tasks`           | Yes    | Create a task          | `{ "title": "string", "subject_id": int? }` | `201` created task / `404` |
| GET    | `/tasks`           | Yes    | List your tasks (filter with `?subject_id=`, `?completed=`, `?q=`) | -               | `200` array of tasks      |
| GET    | `/tasks/{task_id}` | Yes    | Get one of your tasks  | -                                    | `200` task / `404`        |
| PUT    | `/tasks/{task_id}` | Yes    | Update your task       | `{ "title": "string", "completed": bool, "subject_id": int? }` | `200` updated task / `404` |
| DELETE | `/tasks/{task_id}` | Yes    | Delete your task       | -                                    | `200` message / `404`     |
| POST   | `/tasks/{task_id}/subtasks` | Yes | Create a subtask  | `{ "title": "string" }`              | `201` created subtask / `404` |
| GET    | `/tasks/{task_id}/subtasks` | Yes | List a task's subtasks | -                              | `200` array of subtasks / `404` |
| GET    | `/tasks/{task_id}/subtasks/{id}` | Yes | Get one subtask | -                            | `200` subtask / `404`     |
| PUT    | `/tasks/{task_id}/subtasks/{id}` | Yes | Update a subtask | `{ "title": "string", "completed": bool }` | `200` updated subtask / `404` |
| DELETE | `/tasks/{task_id}/subtasks/{id}` | Yes | Delete a subtask | -                            | `200` message / `404`     |

### Subjects

Subjects let a user group tasks (e.g. "Math", "History"). Each subject belongs to
the user who created it, and names are unique per user (a duplicate returns `409`).
A task may optionally reference one subject via `subject_id`; assigning a subject
that isn't yours returns `404`. Deleting a subject does not delete its tasks - the
tasks remain and their `subject_id` is set to `null`. List a subject's tasks with
`GET /tasks?subject_id=<id>`.

### Subtasks

A task can be broken into subtasks (e.g. "Outline", "Draft", "Proofread"), each
with its own `completed` flag that is toggled independently and never changes the
parent task's status. Subtasks live under nested routes
`/tasks/{task_id}/subtasks` and are reached through the parent task, so they
inherit its ownership (another user's task, or an unknown task, returns `404`).

### Search & filtering

`GET /tasks` accepts three optional query params that combine with AND and are
always scoped to your tasks:

- `subject_id=<id>` - only tasks assigned to that subject.
- `completed=true|false` - only completed or only pending tasks (invalid values return `422`).
- `q=<text>` - case-insensitive substring match on the title (e.g. `q=sql` matches "Study SQL"). A blank/whitespace value is ignored, and `%`/`_` are matched literally.

Example: list pending tasks whose title contains "sql":

```bash
curl "http://127.0.0.1:8000/tasks?completed=false&q=sql" \
  -H "Authorization: Bearer $TOKEN"
```
Deleting a task also deletes its subtasks.

### Data Model

A task is represented as:

```json
{
  "id": 1,
  "title": "Study SQL",
  "completed": false,
  "subject_id": null
}
```

A subject is represented as:

```json
{
  "id": 1,
  "name": "Math"
}
```

A subtask is represented as:

```json
{
  "id": 1,
  "title": "Outline",
  "completed": false,
  "task_id": 1
}
```

### Example Requests

All task requests require a bearer token (see [Authentication](#authentication)).

```bash
TOKEN="<JWT from /auth/login>"

# Create a subject
curl -X POST http://127.0.0.1:8000/subjects \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"name": "Math"}'

# Create a task (optionally grouped under a subject)
curl -X POST http://127.0.0.1:8000/tasks \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Study SQL", "subject_id": 1}'

# List your tasks (optionally filtered by subject)
curl "http://127.0.0.1:8000/tasks?subject_id=1" \
  -H "Authorization: Bearer $TOKEN"

# Update a task
curl -X PUT http://127.0.0.1:8000/tasks/1 \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"title": "Study SQL", "completed": true}'

# Delete a task
curl -X DELETE http://127.0.0.1:8000/tasks/1 \
  -H "Authorization: Bearer $TOKEN"
```

## Database Migrations

The database schema is managed with [Alembic](https://alembic.sqlalchemy.org/).
Alembic reads the same `DATABASE_URL` as the application (normalized to the
`postgresql+psycopg://` dialect) and uses the ORM models' metadata as the source
of truth for autogeneration.

```bash
# Apply all migrations to bring the database up to date
alembic upgrade head

# Autogenerate a new migration after changing the ORM models
alembic revision --autogenerate -m "describe your change"

# Inspect/roll back history
alembic current
alembic downgrade -1
```

> If a database already contains the schema (for example from an earlier phase),
> mark it as up to date without re-running DDL with `alembic stamp head`.

The test suite does not run migrations; it builds the schema directly via
`Base.metadata.create_all` for speed and isolation.

## Testing

The test suite uses `pytest` with FastAPI's `TestClient`. Tests run against the
dedicated `student_tasks_test` database, rebuild the schema from the ORM models,
and truncate the `subtasks`, `tasks`, `subjects`, and `users` tables before each
test, so they are isolated and never touch development data. A helper fixture
registers a user and attaches a bearer token for the authenticated endpoints.

Make sure PostgreSQL is running (`docker compose up -d`), then:

```bash
# Run the full suite
pytest

# Run with extra detail / a specific test
pytest -v
pytest tests/test_tasks.py::test_create_task
```

## Roadmap

- [x] CRUD operations with in-memory storage
- [x] Service layer architecture
- [x] SQLite-backed persistence with raw SQL
- [x] Extract routes into dedicated route modules
- [x] Automated test suite with pytest
- [x] Migrate to PostgreSQL with environment-based configuration
- [x] Introduce SQLAlchemy ORM and migrations
- [x] User accounts and JWT authentication (owner-scoped tasks)
- [x] Subjects to group tasks (per-user, optional, filterable)
- [x] Subtasks under tasks (nested, independently completable)
- [x] Search & filtering on tasks (`completed`, `q`, combinable)
- [ ] Containerization and cloud deployment

## Contributing

This project uses the [Conventional Commits](https://www.conventionalcommits.org/) specification for commit messages, for example:

```
feat(tasks): add task completion filtering
fix(database): close connection on error paths
docs: document API endpoints in README
```
