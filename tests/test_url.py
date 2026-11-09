
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.dependency import connect_redis


class FakeRedis:
    def __init__(self):
        self.data = {}

    async def get(self, key):
        return self.data.get(key)

    async def set(self, key, value):
        self.data[key] = value
        return True


@pytest.fixture
def client():
    fake_redis = FakeRedis()

    async def override_redis():
        return fake_redis

    app.dependency_overrides[connect_redis] = override_redis

    with TestClient(app, follow_redirects=False) as test_client:
        yield test_client

    app.dependency_overrides.clear()


def test_create_short_url(client):
    response = client.post(
        "/",
        json={"url": "https://example.com"}
    )

    assert response.status_code == 201
    assert "url" in response.json()
    assert response.json()["url"]


def test_duplicate_url_returns_409(client):
    payload = {"url": "https://example.com"}

    first_response = client.post("/", json=payload)
    second_response = client.post("/", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409


def test_read_short_url_redirects(client):
    original_url = "https://example.com"

    create_response = client.post(
        "/",
        json={"url": original_url}
    )

    short_url = create_response.json()["url"]

    response = client.get(
        "/",
        params={"short_url": short_url}
    )

    assert response.status_code == 302
    assert response.headers["location"] == original_url + "/"


def test_nonexistent_short_url_returns_404(client):
    response = client.get(
        "/",
        params={"short_url": "unknown123"}
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "URL not found"


def test_invalid_url_returns_422(client):
    response = client.post(
        "/",
        json={"url": "this-is-not-a-valid-url"}
    )

    assert response.status_code == 422
