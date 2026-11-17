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
    "params", [{"difficulty": "insane"}, {"category": "categorythatdoesnotexist"},
               {"ordering": "cool_first"}]
)
@pytest.mark.django_db
def test_list_invalid_filters(api_client, params):
    response = api_client.get(reverse("ctf:challenges"), params)

    assert response.status_code == 400


@pytest.mark.django_db
def test_list_page_out_of_range(api_client):
    response = api_client.get(reverse("ctf:challenges"), {"page": 6767})

    assert response.status_code == 404


@pytest.mark.django_db
def test_detail_flag_is_not_leaked(api_client, active_challenge):
    response = api_client.get(reverse("ctf:ind_challenge", kwargs={"pk":
                                                                    active_challenge.id}))

    assert response.status_code == 200
    assert response.data["id"] == active_challenge.id
    assert "flag" not in response.data


@pytest.mark.parametrize(
    "role, expected",
    [("anon", 404), ("other_user", 404), ("user", 200), ("admin", 200)],
)
@pytest.mark.django_db
def test_detail_draft_visibility(role, expected, roles, challenge):
    response = roles[role].get(reverse("ctf:ind_challenge", kwargs={"pk":
                                                                    challenge.id}))

    assert response.status_code == expected


@pytest.mark.django_db
def test_detail_not_found(api_client):
    response = api_client.get(reverse("ctf:ind_challenge", kwargs={"pk": 6767}))

    assert response.status_code == 404


