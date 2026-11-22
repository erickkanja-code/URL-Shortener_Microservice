"""Tests for the URL management endpoints under /api/v1/urls."""

from datetime import timedelta

from app.core.security import REFRESH_TOKEN_TYPE, create_token
from app.services.url import ALPHABET, SHORT_CODE_LENGTH
from tests.helpers import URLS_ENDPOINT, create_url, url_detail


# ---------- Authentication ----------

def test_url_endpoints_require_a_token(client):
    assert client.post(URLS_ENDPOINT, json={"original_url": "https://a.com"}).status_code == 401
    assert client.get(URLS_ENDPOINT).status_code == 401
    assert client.get(url_detail("abc")).status_code == 401
    assert client.put(url_detail("abc"), json={}).status_code == 401
    assert client.delete(url_detail("abc")).status_code == 401


def test_url_endpoints_reject_an_invalid_token(client):
    response = client.get(URLS_ENDPOINT, headers={"Authorization": "Bearer not-a-real-token"})

    assert response.status_code == 401


def test_url_endpoints_reject_a_refresh_token(client, user):
    refresh = create_token(user.id, REFRESH_TOKEN_TYPE, expires_in=timedelta(days=1))

    response = client.get(URLS_ENDPOINT, headers={"Authorization": f"Bearer {refresh}"})

    assert response.status_code == 401


# ---------- Create ----------

def test_create_url_returns_the_new_url(client, user, user_headers):
    response = client.post(
        URLS_ENDPOINT,
        json={"original_url": "https://example.com/page", "tags": ["Marketing"]},
        headers=user_headers,
    )

    assert response.status_code == 201
    body = response.json()
    assert body["original_url"] == "https://example.com/page"
    assert body["owner"] == {"id": user.id, "email": user.email}
    assert body["tags"] == [{"name": "Marketing"}]
    assert body["click_count"] == 0
    assert body["is_active"] is True


def test_create_url_ignores_an_owner_id_in_the_body(client, user, other_user, user_headers):
    body = create_url(client, user_headers, owner_id=other_user.id)

    assert body["owner"]["id"] == user.id


def test_create_url_generates_a_valid_random_short_code(client, user_headers):
    body = create_url(client, user_headers)

    assert len(body["short_code"]) == SHORT_CODE_LENGTH
    assert all(character in ALPHABET for character in body["short_code"])


def test_create_url_uses_custom_alias_as_short_code(client, other_user_headers):
    body = create_url(client, other_user_headers, custom_alias="my-link")

    assert body["short_code"] == "my-link"
    assert body["custom_alias"] == "my-link"


def test_create_url_rejects_a_taken_alias(client, other_user_headers):
    create_url(client, other_user_headers, "https://first.com", custom_alias="my-link")

    response = client.post(
        URLS_ENDPOINT,
        json={"original_url": "https://second.com", "custom_alias": "my-link"},
        headers=other_user_headers,
    )

    assert response.status_code == 409


def test_create_url_rejects_an_invalid_alias(client, user_headers):
    response = client.post(
        URLS_ENDPOINT,
        json={"original_url": "https://example.com", "custom_alias": "has space"},
        headers=user_headers,
    )

    assert response.status_code == 422


def test_same_user_cannot_shorten_the_same_url_twice(client, user_headers):
    create_url(client, user_headers, "https://example.com/page")

    response = client.post(
        URLS_ENDPOINT, json={"original_url": "https://example.com/page"}, headers=user_headers
    )

    assert response.status_code == 409


def test_different_users_can_shorten_the_same_url(client, user_headers, other_user_headers):
    first = create_url(client, user_headers, "https://example.com/page")
    second = create_url(client, other_user_headers, "https://example.com/page")

    assert first["short_code"] != second["short_code"]


def test_create_url_rejects_unknown_tags(client, user_headers):
    response = client.post(
        URLS_ENDPOINT,
        json={"original_url": "https://example.com", "tags": ["Nope"]},
        headers=user_headers,
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Unknown tags: Nope"


def test_create_url_rejects_an_invalid_url(client, user_headers):
    response = client.post(URLS_ENDPOINT, json={"original_url": "not a url"}, headers=user_headers)

    assert response.status_code == 422


# ---------- List and pagination ----------

def test_list_urls_returns_only_the_users_urls(client, user_headers, other_user_headers):
    create_url(client, user_headers, "https://mine.com")
    create_url(client, other_user_headers, "https://theirs.com")

    body = client.get(URLS_ENDPOINT, headers=user_headers).json()

    assert body["total"] == 1
    assert [item["original_url"] for item in body["items"]] == ["https://mine.com/"]


def test_list_urls_paginates_newest_first(client, user_headers):
    for number in range(5):
        create_url(client, user_headers, f"https://example.com/{number}")

    body = client.get(URLS_ENDPOINT, params={"page": 2, "size": 2}, headers=user_headers).json()

    assert body["total"] == 5
    assert body["page"] == 2
    assert body["size"] == 2
    assert [item["original_url"] for item in body["items"]] == [
        "https://example.com/2",
        "https://example.com/1",
    ]


def test_list_urls_returns_an_empty_page_past_the_end(client, user_headers):
    create_url(client, user_headers)

    body = client.get(URLS_ENDPOINT, params={"page": 5}, headers=user_headers).json()

    assert body["total"] == 1
    assert body["items"] == []


def test_list_urls_rejects_invalid_pagination(client, user_headers):
    assert client.get(URLS_ENDPOINT, params={"page": 0}, headers=user_headers).status_code == 422
    assert client.get(URLS_ENDPOINT, params={"size": 101}, headers=user_headers).status_code == 422


# ---------- Retrieve (read-only for non-owners) ----------

def test_get_url_returns_the_owners_url(client, user_headers):
    created = create_url(client, user_headers)

    response = client.get(url_detail(created["short_code"]), headers=user_headers)

    assert response.status_code == 200
    assert response.json()["short_code"] == created["short_code"]


def test_other_users_can_read_a_url(client, user_headers, other_user_headers):
    created = create_url(client, user_headers)

    response = client.get(url_detail(created["short_code"]), headers=other_user_headers)

    assert response.status_code == 200


def test_get_url_returns_404_for_unknown_code(client, user_headers):
    response = client.get(url_detail("unknown"), headers=user_headers)

    assert response.status_code == 404


# ---------- Update (owner only) ----------

def test_update_url_changes_only_the_fields_sent(client, user_headers):
    created = create_url(client, user_headers, title="Old title", description="Keep me")

    response = client.put(
        url_detail(created["short_code"]), json={"title": "New title"}, headers=user_headers
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "New title"
    assert body["description"] == "Keep me"


def test_update_url_replaces_tags(client, user_headers):
    created = create_url(client, user_headers, tags=["Marketing"])

    body = client.put(
        url_detail(created["short_code"]), json={"tags": ["Work", "News"]}, headers=user_headers
    ).json()

    assert sorted(tag["name"] for tag in body["tags"]) == ["News", "Work"]


def test_other_users_cannot_update_a_url(client, user_headers, other_user_headers):
    created = create_url(client, user_headers, title="Original")

    response = client.put(
        url_detail(created["short_code"]), json={"title": "Hacked"}, headers=other_user_headers
    )

    assert response.status_code == 403
    body = client.get(url_detail(created["short_code"]), headers=user_headers).json()
    assert body["title"] == "Original"


def test_update_url_returns_404_for_unknown_code(client, user_headers):
    response = client.put(url_detail("unknown"), json={"title": "x"}, headers=user_headers)

    assert response.status_code == 404


# ---------- Delete (owner only, deactivates) ----------

def test_delete_url_deactivates_instead_of_deleting(client, user_headers):
    created = create_url(client, user_headers)

    response = client.delete(url_detail(created["short_code"]), headers=user_headers)

    assert response.status_code == 204
    body = client.get(url_detail(created["short_code"]), headers=user_headers).json()
    assert body["is_active"] is False


def test_other_users_cannot_delete_a_url(client, user_headers, other_user_headers):
    created = create_url(client, user_headers)

    response = client.delete(url_detail(created["short_code"]), headers=other_user_headers)

    assert response.status_code == 403
    body = client.get(url_detail(created["short_code"]), headers=user_headers).json()
    assert body["is_active"] is True


# ---------- Tag search ----------

def test_list_urls_filters_by_tag(client, user_headers):
    create_url(client, user_headers, "https://a.com", tags=["Marketing"])
    create_url(client, user_headers, "https://b.com", tags=["Work"])
    create_url(client, user_headers, "https://c.com", tags=["Marketing", "Work"])

    body = client.get(URLS_ENDPOINT, params={"tag": "Marketing"}, headers=user_headers).json()

    assert body["total"] == 2
    assert sorted(item["original_url"] for item in body["items"]) == [
        "https://a.com/",
        "https://c.com/",
    ]


def test_tag_search_ignores_case(client, user_headers):
    create_url(client, user_headers, tags=["Marketing"])

    body = client.get(URLS_ENDPOINT, params={"tag": "marKETing"}, headers=user_headers).json()

    assert body["total"] == 1


def test_tag_search_returns_each_url_once(client, user_headers):
    create_url(client, user_headers, tags=["Marketing", "Work", "News"])

    body = client.get(URLS_ENDPOINT, params={"tag": "Work"}, headers=user_headers).json()

    assert body["total"] == 1
    assert len(body["items"]) == 1


def test_tag_search_with_an_unknown_tag_returns_nothing(client, user_headers):
    create_url(client, user_headers, tags=["Marketing"])

    body = client.get(URLS_ENDPOINT, params={"tag": "Nope"}, headers=user_headers).json()

    assert body["total"] == 0
    assert body["items"] == []


def test_tag_search_only_includes_the_users_urls(client, user_headers, other_user_headers):
    create_url(client, user_headers, "https://mine.com", tags=["Marketing"])
    create_url(client, other_user_headers, "https://theirs.com", tags=["Marketing"])

    body = client.get(URLS_ENDPOINT, params={"tag": "Marketing"}, headers=user_headers).json()

    assert [item["original_url"] for item in body["items"]] == ["https://mine.com/"]


def test_tag_search_works_with_pagination(client, user_headers):
    for number in range(3):
        create_url(client, user_headers, f"https://tagged.com/{number}", tags=["Work"])
    create_url(client, user_headers, "https://untagged.com")

    body = client.get(
        URLS_ENDPOINT, params={"tag": "Work", "page": 2, "size": 2}, headers=user_headers
    ).json()

    assert body["total"] == 3
    assert [item["original_url"] for item in body["items"]] == ["https://tagged.com/0"]