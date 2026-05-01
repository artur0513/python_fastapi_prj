import pytest
from fastapi.testclient import TestClient
from sqlmodel import SQLModel, Session, create_engine
from app.database import get_session
from app.main import app
from faker import Faker

fake = Faker()

# Тестовый движок БД
test_engine = create_engine("sqlite:///./test.db", echo=False)


def override_get_session():
    with Session(test_engine) as session:
        yield session


app.dependency_overrides[get_session] = override_get_session


@pytest.fixture(autouse=True)
def setup_db():
    """Пересоздаёт таблицы перед каждым тестом."""
    SQLModel.metadata.create_all(test_engine)
    yield
    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture
def client():
    return TestClient(app)


# Фикстура, которую используют тесты auth
@pytest.fixture
def fake_data():
    return {
        "email": fake.email(),
        "password": fake.password(),
        "full_name": fake.name(),
        "role": "courier"
    }


# ---------- вспомогательные функции ----------
def register_and_login(client, role):
    email = fake.email()
    password = fake.password()
    name = fake.name()
    resp = client.post("/auth/signup", json={
        "email": email,
        "password": password,
        "full_name": name,
        "role": role
    })
    assert resp.status_code == 201
    resp = client.post("/auth/login", data={
        "username": email,
        "password": password
    })
    assert resp.status_code == 200
    return resp.json()["access_token"]


@pytest.fixture
def manager_token(client):
    return register_and_login(client, "manager")


@pytest.fixture
def courier_token(client):
    return register_and_login(client, "courier")


@pytest.fixture
def sample_pickup_point_id(client, manager_token):
    resp = client.post(
        "/pickup-points",
        json={"name": "ПВЗ", "address": "Москва", "latitude": 55.0, "longitude": 37.0},
        headers={"Authorization": f"Bearer {manager_token}"}
    )
    return resp.json()["id"]


@pytest.fixture
def sample_courier_id(client):
    """Создаёт курьера и возвращает его ID (без токена)."""
    email = fake.email()
    resp = client.post("/auth/signup", json={
        "email": email,
        "password": "pass",
        "full_name": "Test Courier",
        "role": "courier"
    })
    assert resp.status_code == 201
    return resp.json()["id"]
