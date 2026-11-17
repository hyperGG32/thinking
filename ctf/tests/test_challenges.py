import pytest

from hashlib import sha256

from django.urls import reverse

from ctf.models import Challenge
from .conftest import NEW_FLAG

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


@pytest.mark.django_db
def test_create_requires_auth(api_client, challenge_body):
    response = api_client.post(reverse("ctf:challenges"), challenge_body, format="json")

    assert response.status_code == 401
    assert not Challenge.objects.exists()


@pytest.mark.django_db
def test_create_with_invalid_token(api_client, challenge_body):
    api_client.credentials(HTTP_AUTHORIZATION="Bearer Sometextthatisntvalidlol")

    response = api_client.post(reverse("ctf:challenges"), challenge_body, format="json")

    assert response.status_code == 401


@pytest.mark.django_db
def test_create_challenge(roles, user, challenge_body):
    response = roles["user"].post(reverse("ctf:challenges"), challenge_body,
                                  format="json")

    assert response.status_code == 201
    assert response.data["author"]["id"] == user.id
    assert response.data["status"] == "draft"
    assert "flag" not in response.data

    saved = Challenge.objects.get(pk=response.data["id"])
    assert saved.flag == sha256(NEW_FLAG.encode()).hexdigest()


@pytest.mark.django_db
def test_create_invalid_data(roles, category):
    body = {"title": "x", "category": category.id, "difficulty": "zzz", "points": -1}

    response = roles["user"].post(reverse("ctf:challenges"), body, format="json")

    assert response.status_code == 400
    assert ({"difficulty", "points", "description", "flag"} <=
            set(response.data["fields"]))
    assert not Challenge.objects.exists()


@pytest.mark.parametrize(
    "role, expected",
    [("anon", 401), ("other_user", 403), ("user", 200), ("admin", 200)],
)
@pytest.mark.django_db
def test_update_permissions(role, expected, roles, challenge):
    url = reverse("ctf:ind_challenge", kwargs={"pk": challenge.id})

    response = roles[role].patch(url, {"points": 676}, format="json")

    assert response.status_code == expected
    challenge.refresh_from_db()
    assert challenge.points == (676 if expected == 200 else 67)


@pytest.mark.parametrize(
    "role, start, target, expected",
    [
        ("user", "draft", "review", 200),
        ("user", "review", "active", 403),
        ("admin", "review", "active", 200),
        ("admin", "review", "rejected", 200),
        ("admin", "active", "draft", 409),
        ("user", "draft", "abc", 400),
    ],
)
@pytest.mark.django_db
def test_update_status_transmission(role, start, target, expected, roles, challenge):
    challenge.status = start
    challenge.save()

    url = reverse("ctf:ind_challenge", kwargs={"pk": challenge.id})
    response = roles[role].patch(url, {"status": target}, format="json")

    assert response.status_code == expected
    challenge.refresh_from_db()
    assert challenge.status == (target if response.status_code == 200 else start)


@pytest.mark.django_db
def test_update_not_found(roles):
    url = reverse("ctf:ind_challenge", kwargs={"pk": 6767})

    response = roles["admin"].patch(url, {"points": 228}, format="json")

    assert response.status_code == 404


@pytest.mark.parametrize(
    "role, expected",
    [("anon", 401), ("other_user", 403), ("user", 204), ("admin", 204)],
)
@pytest.mark.django_db
def test_delete_permissions(role, expected, roles, challenge):
    url = reverse("ctf:ind_challenge", kwargs={"pk": challenge.id})

    response = roles[role].delete(url)

    assert response.status_code == expected
    assert Challenge.objects.filter(id=challenge.id).exists() == (expected != 204)


@pytest.mark.django_db
def test_delete_not_found(roles):
    url = reverse("ctf:ind_challenge", kwargs={"pk":6767})

    response = roles["admin"].delete(url)

    assert response.status_code == 404


@pytest.mark.django_db
def test_login_token_works(api_client, user, challenge_body):
    tokens = api_client.post(
        reverse("accounts:token_obtain_pair"),
        {"username": user.username, "password": "N0th4xx4bl3_1337$"},
        format="json"
    ).data

    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

    response = api_client.post(reverse("ctf:challenges"), challenge_body, format="json")

    assert response.status_code == 201
    assert response.data["author"]["id"] == user.id


@pytest.mark.django_db
def test_create_logs_without_secrets(roles, challenge_body, caplog):
    caplog.set_level("INFO", logger="ctf")

    response = roles["user"].post(reverse("ctf:challenges"), challenge_body, format="json")

    assert response.status_code == 201
    assert f"Challenge {response.data['id']} created" in caplog.text
    assert NEW_FLAG not in caplog.text
