"""Tests for URL input sanitization.

Every URL sent to the API is checked before any business logic runs.
Unsafe URLs are rejected with 422.
"""

import pytest

from app.schemas.url import MAX_URL_LENGTH
from tests.helpers import URLS_ENDPOINT, create_url, url_detail


@pytest.mark.parametrize(
    "unsafe_url",
    [
        "javascript:alert(1)",                    # script execution
        "data:text/html,<script>alert(1)</script>",  # inline content
        "ftp://example.com/file",                 # not http or https
        "https://user:secret@example.com/",       # embedded credentials
        "http://localhost:8000/admin",            # this machine
        "http://127.0.0.1/",                      # loopback IPv4
        "http://[::1]/",                          # loopback IPv6
        "http://192.168.1.1/router",              # private network
        "http://10.0.0.5/",                       # private network
        "http://169.254.169.254/latest/meta-data",  # link-local (cloud metadata)
        "http://0.0.0.0/",                        # unspecified address
        "not a url",
    ],
)
def test_create_url_rejects_unsafe_urls(client, user_headers, unsafe_url):
    response = client.post(URLS_ENDPOINT, json={"original_url": unsafe_url}, headers=user_headers)

    assert response.status_code == 422


def test_create_url_rejects_urls_longer_than_the_column(client, user_headers):
    too_long = "https://example.com/" + "a" * MAX_URL_LENGTH

    response = client.post(URLS_ENDPOINT, json={"original_url": too_long}, headers=user_headers)

    assert response.status_code == 422


def test_create_url_accepts_a_public_ip_address(client, user_headers):
    body = create_url(client, user_headers, "http://93.184.216.34/page")

    assert body["original_url"] == "http://93.184.216.34/page"


def test_create_url_normalizes_the_url(client, user_headers):
    body = create_url(client, user_headers, "  HTTPS://Example.COM/a b  ")

    assert body["original_url"] == "https://example.com/a%20b"


def test_create_url_strips_whitespace_from_text_fields(client, user_headers):
    body = create_url(client, user_headers, title="  My title  ", description="\tNotes\n")

    assert body["title"] == "My title"
    assert body["description"] == "Notes"


def test_update_url_rejects_unsafe_urls(client, user_headers):
    created = create_url(client, user_headers)

    response = client.put(
        url_detail(created["short_code"]),
        json={"original_url": "http://127.0.0.1/"},
        headers=user_headers,
    )

    assert response.status_code == 422