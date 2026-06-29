import os
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/student_tasks_test",
)


@pytest.fixture(scope="session", autouse=True)
def _configure_test_environment() -> None:
    """Point the app at the disposable test database and a fixed JWT secret."""
    os.environ["DATABASE_URL"] = TEST_DATABASE_URL
    os.environ["SECRET_KEY"] = "test-secret-key-that-is-at-least-32-bytes-long"


@pytest.fixture(scope="session", autouse=True)
def _reset_schema(_configure_test_environment) -> None:
    """Rebuild the test schema from the current models (drops stale tables)."""
    from app.database.database import Base, engine
    from app import models  # noqa: F401  register models on Base.metadata

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


@pytest.fixture
def client() -> Iterator[TestClient]:
    """Provide an unauthenticated TestClient backed by a clean test database.

    Entering the TestClient context runs the app's lifespan handler, which creates
    the schema via ``Base.metadata.create_all``. The ``tasks`` and ``users`` tables
    are then truncated so each test starts empty with ids reset to 1.
    """
    from sqlalchemy import text

    from app.database.database import engine
    from app.main import app

    with TestClient(app) as test_client:
        with engine.begin() as connection:
            connection.execute(
                text("TRUNCATE tasks, users RESTART IDENTITY CASCADE")
            )
        yield test_client


def register_and_login(
    client: TestClient,
    email: str = "user@example.com",
    password: str = "password123",
) -> str:
    """Register a user and return a bearer access token."""
    client.post("/auth/register", json={"email": email, "password": password})
    response = client.post(
        "/auth/login",
        data={"username": email, "password": password},
    )
    return response.json()["access_token"]


@pytest.fixture
def auth_client(client: TestClient) -> TestClient:
    """A TestClient with a registered user's Authorization header preset."""
    token = register_and_login(client)
    client.headers["Authorization"] = f"Bearer {token}"
    return client
