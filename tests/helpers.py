"""Small helpers and constants that keep the tests short and readable."""

from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.models import User

URLS_ENDPOINT = "/api/v1/urls/"
REGISTER_ENDPOINT = "/api/v1/auth/register/"
LOGIN_ENDPOINT = "/api/v1/auth/login/"
REFRESH_ENDPOINT = "/api/v1/auth/refresh/"
TEST_PASSWORD = "correct-password"


def auth_headers(user: User) -> dict:
    """Return request headers carrying a valid access token for the user."""
    return {"Authorization": f"Bearer {create_access_token(user.id)}"}


def url_detail(short_code: str) -> str:
    """Return the path of one URL's endpoints, such as /api/v1/urls/abc/."""
    return f"{URLS_ENDPOINT}{short_code}/"


def create_url(
    client: TestClient,
    headers: dict,
    original_url: str = "https://example.com/page",
    **fields,
) -> dict:
    """Create a URL as the user in `headers` and return the response body.

    Extra fields (such as `tags` or `custom_alias`) are added to the request.
    Fails the test immediately if the API does not return 201.
    """
    response = client.post(
        URLS_ENDPOINT,
        json={"original_url": original_url, **fields},
        headers=headers,
    )
    assert response.status_code == 201, response.text
    return response.json()


def login(client: TestClient, email: str, password: str = TEST_PASSWORD) -> dict:
    """Log in through the API and return the token pair.

    Fails the test immediately if the API does not return 200.
    """
    response = client.post(LOGIN_ENDPOINT, json={"email": email, "password": password})
    assert response.status_code == 200, response.text
    return response.json()