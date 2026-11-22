"""Tests for the authentication endpoints under /api/v1/auth."""

from sqlalchemy import select

from app.core.security import verify_password
from app.models import User
from tests.helpers import REGISTER_ENDPOINT, TEST_PASSWORD


# ---------- Register ----------

def test_register_creates_a_free_account(client):
    response = client.post(
        REGISTER_ENDPOINT, json={"email": "new@example.com", "password": TEST_PASSWORD}
    )

    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "new@example.com"
    assert body["tier"] == "Free"
    assert body["is_premium"] is False


def test_register_never_returns_the_password(client):
    body = client.post(
        REGISTER_ENDPOINT, json={"email": "new@example.com", "password": TEST_PASSWORD}
    ).json()

    assert "password" not in body
    assert "hashed_password" not in body


def test_register_stores_a_hash_not_the_password(client, db_session):
    client.post(REGISTER_ENDPOINT, json={"email": "new@example.com", "password": TEST_PASSWORD})

    user = db_session.scalars(select(User).where(User.email == "new@example.com")).one()
    assert user.hashed_password != TEST_PASSWORD
    assert user.hashed_password.startswith("$argon2")
    assert verify_password(TEST_PASSWORD, user.hashed_password)


def test_register_rejects_a_duplicate_email_in_any_case(client):
    client.post(REGISTER_ENDPOINT, json={"email": "new@example.com", "password": TEST_PASSWORD})

    response = client.post(
        REGISTER_ENDPOINT, json={"email": "NEW@Example.com", "password": TEST_PASSWORD}
    )

    assert response.status_code == 409


def test_register_rejects_an_invalid_email(client):
    response = client.post(
        REGISTER_ENDPOINT, json={"email": "not-an-email", "password": TEST_PASSWORD}
    )

    assert response.status_code == 422


def test_register_rejects_a_short_password(client):
    response = client.post(
        REGISTER_ENDPOINT, json={"email": "new@example.com", "password": "short"}
    )

    assert response.status_code == 422