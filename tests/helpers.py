"""Small helpers and constants that keep the tests short and readable."""

from fastapi.testclient import TestClient

URLS_ENDPOINT = "/api/v1/urls/"
REGISTER_ENDPOINT = "/api/v1/auth/register/"
TEST_PASSWORD = "correct-password"


def create_url(
    client: TestClient,
    owner_id: int,
    original_url: str = "https://example.com/page",
    **fields,
) -> dict:
    """Create a URL through the API and return the response body.

    Extra fields (such as `tags` or `custom_alias`) are added to the request.
    Fails the test immediately if the API does not return 201.
    """
    response = client.post(
        URLS_ENDPOINT,
        json={"original_url": original_url, "owner_id": owner_id, **fields},
    )
    assert response.status_code == 201, response.text
    return response.json()