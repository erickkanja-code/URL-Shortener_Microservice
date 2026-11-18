"""Tests for the URL management endpoints under /api/v1/urls."""

from app.services.url import ALPHABET, SHORT_CODE_LENGTH
from tests.helpers import URLS_ENDPOINT, create_url


# ---------- Create ----------

def test_create_url_returns_the_new_url(client, user):
    response = client.post(
        URLS_ENDPOINT,
        json={"original_url": "https://example.com/page", "owner_id": user.id, "tags": ["Marketing"]},
    )

    assert response.status_code == 201
    body = response.json()
    assert body["original_url"] == "https://example.com/page"
    assert body["owner"] == {"id": user.id, "email": user.email}
    assert body["tags"] == [{"name": "Marketing"}]
    assert body["click_count"] == 0
    assert body["is_active"] is True


def test_create_url_generates_a_valid_random_short_code(client, user):
    body = create_url(client, user.id)

    assert len(body["short_code"]) == SHORT_CODE_LENGTH
    assert all(character in ALPHABET for character in body["short_code"])


def test_create_url_uses_custom_alias_as_short_code(client, user):
    body = create_url(client, user.id, custom_alias="my-link")

    assert body["short_code"] == "my-link"
    assert body["custom_alias"] == "my-link"


def test_create_url_rejects_a_taken_alias(client, user, other_user):
    create_url(client, user.id, custom_alias="my-link")

    response = client.post(
        URLS_ENDPOINT,
        json={"original_url": "https://other.com", "owner_id": other_user.id, "custom_alias": "my-link"},
    )

    assert response.status_code == 409


def test_create_url_rejects_an_invalid_alias(client, user):
    response = client.post(
        URLS_ENDPOINT,
        json={"original_url": "https://example.com", "owner_id": user.id, "custom_alias": "has space"},
    )

    assert response.status_code == 422


def test_same_user_cannot_shorten_the_same_url_twice(client, user):
    create_url(client, user.id, "https://example.com/page")

    response = client.post(
        URLS_ENDPOINT, json={"original_url": "https://example.com/page", "owner_id": user.id}
    )

    assert response.status_code == 409


def test_different_users_can_shorten_the_same_url(client, user, other_user):
    first = create_url(client, user.id, "https://example.com/page")
    second = create_url(client, other_user.id, "https://example.com/page")

    assert first["short_code"] != second["short_code"]


def test_create_url_rejects_unknown_tags(client, user):
    response = client.post(
        URLS_ENDPOINT,
        json={"original_url": "https://example.com", "owner_id": user.id, "tags": ["Nope"]},
    )

    assert response.status_code == 400
    assert response.json()["detail"] == "Unknown tags: Nope"


def test_create_url_rejects_an_unknown_owner(client):
    response = client.post(URLS_ENDPOINT, json={"original_url": "https://example.com", "owner_id": 999})

    assert response.status_code == 404


def test_create_url_rejects_an_invalid_url(client, user):
    response = client.post(URLS_ENDPOINT, json={"original_url": "not a url", "owner_id": user.id})

    assert response.status_code == 422


# ---------- List and pagination ----------

def test_list_urls_returns_only_the_owners_urls(client, user, other_user):
    create_url(client, user.id, "https://mine.com")
    create_url(client, other_user.id, "https://theirs.com")

    body = client.get(URLS_ENDPOINT, params={"owner_id": user.id}).json()

    assert body["total"] == 1
    assert [item["original_url"] for item in body["items"]] == ["https://mine.com/"]


def test_list_urls_paginates_newest_first(client, user):
    for number in range(5):
        create_url(client, user.id, f"https://example.com/{number}")

    body = client.get(URLS_ENDPOINT, params={"owner_id": user.id, "page": 2, "size": 2}).json()

    assert body["total"] == 5
    assert body["page"] == 2
    assert body["size"] == 2
    assert [item["original_url"] for item in body["items"]] == [
        "https://example.com/2",
        "https://example.com/1",
    ]


def test_list_urls_returns_an_empty_page_past_the_end(client, user):
    create_url(client, user.id)

    body = client.get(URLS_ENDPOINT, params={"owner_id": user.id, "page": 5}).json()

    assert body["total"] == 1
    assert body["items"] == []


def test_list_urls_rejects_invalid_pagination(client, user):
    assert client.get(URLS_ENDPOINT, params={"owner_id": user.id, "page": 0}).status_code == 422
    assert client.get(URLS_ENDPOINT, params={"owner_id": user.id, "size": 101}).status_code == 422


# ---------- Retrieve ----------

def test_get_url_returns_the_owners_url(client, user):
    created = create_url(client, user.id)

    response = client.get(f"{URLS_ENDPOINT}{created['short_code']}/", params={"owner_id": user.id})

    assert response.status_code == 200
    assert response.json()["short_code"] == created["short_code"]


def test_get_url_hides_other_users_urls(client, user, other_user):
    created = create_url(client, user.id)

    response = client.get(
        f"{URLS_ENDPOINT}{created['short_code']}/", params={"owner_id": other_user.id}
    )

    assert response.status_code == 404


def test_get_url_returns_404_for_unknown_code(client, user):
    response = client.get(f"{URLS_ENDPOINT}unknown/", params={"owner_id": user.id})

    assert response.status_code == 404


# ---------- Update ----------

def test_update_url_changes_only_the_fields_sent(client, user):
    created = create_url(client, user.id, title="Old title", description="Keep me")

    response = client.put(
        f"{URLS_ENDPOINT}{created['short_code']}/", json={"owner_id": user.id, "title": "New title"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["title"] == "New title"
    assert body["description"] == "Keep me"


def test_update_url_replaces_tags(client, user):
    created = create_url(client, user.id, tags=["Marketing"])

    body = client.put(
        f"{URLS_ENDPOINT}{created['short_code']}/", json={"owner_id": user.id, "tags": ["Work", "News"]}
    ).json()

    assert sorted(tag["name"] for tag in body["tags"]) == ["News", "Work"]


def test_update_url_rejects_other_users(client, user, other_user):
    created = create_url(client, user.id)

    response = client.put(
        f"{URLS_ENDPOINT}{created['short_code']}/", json={"owner_id": other_user.id, "title": "Hacked"}
    )

    assert response.status_code == 404


# ---------- Delete (deactivate) ----------

def test_delete_url_deactivates_instead_of_deleting(client, user):
    created = create_url(client, user.id)
    detail_url = f"{URLS_ENDPOINT}{created['short_code']}/"

    response = client.delete(detail_url, params={"owner_id": user.id})

    assert response.status_code == 204
    body = client.get(detail_url, params={"owner_id": user.id}).json()
    assert body["is_active"] is False


def test_delete_url_rejects_other_users(client, user, other_user):
    created = create_url(client, user.id)

    response = client.delete(
        f"{URLS_ENDPOINT}{created['short_code']}/", params={"owner_id": other_user.id}
    )

    assert response.status_code == 404