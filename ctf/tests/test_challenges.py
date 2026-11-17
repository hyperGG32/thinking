import pytest

from django.urls import reverse


@pytest.mark.parametrize(
    "role, sees_draft",
    [("anon", False), ("other_user", False), ("user", True), ("admin", True)],
)
@pytest.mark.django_db
def test_list_visibility(role, sees_draft, roles, challenge, active_challenge):
    response = roles[role].get(reverse("ctf:challenges"))

    assert response.status_code == 200
    ids = {c["id"] for c in response.data["results"]}
    expected = {active_challenge.id, challenge.id} if sees_draft else {active_challenge.id}
    assert ids == expected


@pytest.mark.parametrize(
    "params", [{"difficulty": "zzz"}, {"category": "abc"}, {"ordering": "title"}]
)
@pytest.mark.django_db
def test_list_invalid_filters(api_client, params):
    response = api_client.get(reverse("ctf:challenges"), params)

    assert response.status_code == 400


@pytest.mark.django_db
def test_list_page_out_of_range(api_client):
    response = api_client.get(reverse("ctf:challenges"), {"page": 6767})

    assert response.status_code == 404





