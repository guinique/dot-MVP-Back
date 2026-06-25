import os

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

os.environ.setdefault("SECRET_KEY", "test-secret-key-for-pytest-only")
os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("EMBED_API_KEY", "test-embed-key")
os.environ.setdefault("LLM_PROVIDER", "mock")

from app.database import Base, get_db  # noqa: E402
from app.main import app  # noqa: E402

test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(autouse=True)
def setup_db():
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)


@pytest.fixture
def db():
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _login(client, email: str, password: str) -> str:
    response = client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def _auth_header(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_user(db):
    from app.models.user import UserRole
    from app.schemas.auth import UserCreate
    from app.services import auth as auth_service

    return auth_service.create_user(
        db,
        UserCreate(email="admin@test.com", password="adminpass1", full_name="Admin"),
        role=UserRole.ADMIN,
    )


@pytest.fixture
def admin_headers(client, admin_user):
    token = _login(client, admin_user.email, "adminpass1")
    return _auth_header(token)


@pytest.fixture
def regular_user(db):
    from app.schemas.auth import UserCreate
    from app.services import auth as auth_service

    return auth_service.create_user(
        db,
        UserCreate(email="user@test.com", password="userpass1", full_name="Regular User"),
    )


@pytest.fixture
def user_headers(client, regular_user):
    token = _login(client, regular_user.email, "userpass1")
    return _auth_header(token)


@pytest.fixture
def embed_headers():
    return {"X-Embed-Token": "test-embed-key"}


@pytest.fixture
def sample_tutor(db):
    from app.schemas.tutor import TutorCreate
    from app.services import tutors as tutors_service

    return tutors_service.create_tutor(
        db,
        TutorCreate(
            title="Python Tutor",
            description="Helps with Python basics",
            system_instructions="You are a friendly Python programming tutor.",
            source_urls=["https://example.com/python.txt"],
        ),
    )
