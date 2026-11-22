"""Tests for the authentication endpoints under /api/v1/auth."""

from datetime import timedelta

from sqlalchemy import select

from app.core.security import (
    ACCESS_TOKEN_TYPE,
    REFRESH_TOKEN_TYPE,
    create_token,
    decode_token,
    verify_password,
)
from app.models import User
from tests.helpers import (
    LOGIN_ENDPOINT,
    REFRESH_ENDPOINT,
    REGISTER_ENDPOINT,
    TEST_PASSWORD,
    login,
)


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


# ---------- Login ----------

def test_login_returns_an_access_and_a_refresh_token(client, user):
    body = login(client, user.email)

    assert body["token_type"] == "bearer"
    assert decode_token(body["access_token"], ACCESS_TOKEN_TYPE) == user.id
    assert decode_token(body["refresh_token"], REFRESH_TOKEN_TYPE) == user.id


def test_login_ignores_email_case(client, user):
    body = login(client, user.email.upper())

    assert decode_token(body["access_token"], ACCESS_TOKEN_TYPE) == user.id


def test_login_rejects_a_wrong_password(client, user):
    response = client.post(LOGIN_ENDPOINT, json={"email": user.email, "password": "wrong-password"})

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


def test_login_gives_the_same_error_for_an_unknown_email(client):
    response = client.post(
        LOGIN_ENDPOINT, json={"email": "nobody@example.com", "password": TEST_PASSWORD}
    )

    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"


# ---------- Refresh ----------

def test_refresh_returns_a_new_access_token(client, user):
    tokens = login(client, user.email)

    response = client.post(REFRESH_ENDPOINT, json={"refresh_token": tokens["refresh_token"]})

    assert response.status_code == 200
    assert decode_token(response.json()["access_token"], ACCESS_TOKEN_TYPE) == user.id


def test_refresh_rejects_an_access_token(client, user):
    tokens = login(client, user.email)

    response = client.post(REFRESH_ENDPOINT, json={"refresh_token": tokens["access_token"]})

    assert response.status_code == 401


def test_refresh_rejects_an_expired_token(client, user):
    expired = create_token(user.id, REFRESH_TOKEN_TYPE, expires_in=timedelta(seconds=-1))

    response = client.post(REFRESH_ENDPOINT, json={"refresh_token": expired})

    assert response.status_code == 401


def test_refresh_rejects_a_tampered_token(client, user):
    token = login(client, user.email)["refresh_token"]
    tampered = token[:-4] + ("aaaa" if not token.endswith("aaaa") else "bbbb")

    response = client.post(REFRESH_ENDPOINT, json={"refresh_token": tampered})

    assert response.status_code == 401


def test_refresh_rejects_a_token_for_a_deleted_user(client, db_session, user):
    tokens = login(client, user.email)
    db_session.delete(user)
    db_session.commit()

    response = client.post(REFRESH_ENDPOINT, json={"refresh_token": tokens["refresh_token"]})

    assert response.status_code == 401