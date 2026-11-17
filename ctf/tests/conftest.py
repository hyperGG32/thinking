import pytest

from hashlib import sha256

from django.contrib.auth.models import User
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from ctf.models import Challenge, Category


FLAG = "CTF{t3stLM40_n0t_s33n_0PS3C}"


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def user():
    return User.objects.create_user(username="hacker_test1337",
                                    email="OPSECdemon@opsec.onion",
                                    password="N0th4xx4bl3_1337$")


@pytest.fixture
def other_user():
    return User.objects.create_user(username="opsecangel",
                                    email="OPSECangel@proton.me",
                                    password="wh1t3h4tpr0$w33T")


@pytest.fixture
def admin():
    return User.objects.create_user(username="AdminGodCreator",
                                    email="admin@administartors.org",
                                    password="ADM!Ndeliberatelyh4rdp4$$",
                                    is_staff=True)


@pytest.fixture
def auth_client():
    def make(user):
        client = APIClient()
        token = RefreshToken.for_user(user).access_token
        client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        return client
    return make


@pytest.fixture
def category():
    return Category.objects.create(name="test_category")


@pytest.fixture
def challenge(user, category):
    return Challenge.objects.create(
        title="test challenge",
        description="challenge fixture for testing that should not be in prod if seen in prod huge alarm danger",
        category=category,
        difficulty="hard",
        points=67,
        flag=sha256(FLAG.encode()).hexdigest(),
        author=user,
        status="draft"
    )


@pytest.fixture
def roles(api_client, auth_client, user, other_user, admin):
    return {
        "anon": api_client,
        "user": auth_client(user),
        "other_user": auth_client(other_user),
        "admin": auth_client(admin)
    }


@pytest.fixture
def active_challenge(other_user, category):
    return Challenge.objects.create(category=category, author=other_user, points=67,
                                    status="active", title="test", description="test",
                                    difficulty="easy",
                                    flag=sha256(b"CTF{bactive}").hexdigest())
