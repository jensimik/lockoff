import pyotp
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from lockoff.routers.auth import send_email, send_mobile


@pytest.mark.parametrize(
    ["url", "expected_status_code"],
    (
        ("/healtz", 200),
        ("/some_random_url", 404),
        ("/wrongtoken/qr-code.png", 400),
        ("/wrongtoken/membership-card.pdf", 400),
        ("/wrongtoken/membership-card.pkpass", 400),
        ("/me", 401),
        ("/admin/wrongtoken/qr-code.png", 400),
        ("/admin/access-log", 401),
        ("/admin/system-status", 401),
    ),
)
def test_endpoint_generic(url, expected_status_code, client: TestClient):
    response = client.get(url)
    assert response.status_code == expected_status_code


@pytest.mark.parametrize(
    ["user_id", "ok"],
    (
        (0, True),  # normal user
        (5, True),  # morning user
        (9, False),  # inactive user
    ),
)
def test_request_totp_mobile(user_id, ok, mocker, client: TestClient):
    mobile = f"1000100{user_id}"
    mock = mocker.patch("fastapi.BackgroundTasks.add_task")
    data = {"username": mobile, "username_type": "mobile"}
    response = client.post("/request-totp", json=data)

    assert response.status_code == status.HTTP_200_OK
    if ok:
        mock.assert_called_once()
        mock.assert_called_with(send_mobile, user_id=user_id, message=mocker.ANY)
    else:
        mock.assert_not_called()


@pytest.mark.parametrize(
    ["user_id", "ok"],
    (
        (0, True),  # normal user
        (5, True),  # morning user
        (9, False),  # inactive user
    ),
)
def test_request_totp_email(user_id, ok, mocker, client: TestClient):
    email = f"test{user_id}@test.dk"
    mock = mocker.patch("fastapi.BackgroundTasks.add_task")
    data = {"username": email, "username_type": "email"}
    response = client.post("/request-totp", json=data)

    assert response.status_code == status.HTTP_200_OK
    if ok:
        mock.assert_called_once()
        mock.assert_called_with(send_email, user_id=user_id, message=mocker.ANY)
    else:
        mock.assert_not_called()


@pytest.mark.parametrize(
    ["user_id", "use_correct_totp", "ok"],
    (
        (0, True, True),  # normal user, correct_totp
        (5, True, True),  # morning user, correct totp
        (9, True, False),  # inactive user, correct totp
        (0, False, False),  # normal user, wrong totp
        (5, False, False),  # morning user, wrong totp
        (9, False, False),  # inactive user, wrong totp
    ),
)
def test_login_mobile(user_id, use_correct_totp, ok, client: TestClient):
    mobile = f"1000100{user_id}"
    totp = pyotp.TOTP("H6IC425Q5IFZYAP4VINKRVHX7ZIEKO7E")
    totp_wrong = pyotp.TOTP("6LRKMVJQR7T4GHQ5CZIVKBPMRFRBV7JR")
    data = {
        "username": mobile,
        "username_type": "mobile",
        "totp": totp.now() if use_correct_totp else totp_wrong.now(),
    }
    response = client.post("/login", json=data)
    json = response.json()
    if ok:
        assert response.status_code == status.HTTP_200_OK
        assert "access_token" in json
        assert "token_type" in json
    else:
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert "access_token" not in json
        assert "token_type" not in json


def test_me(aclient: TestClient):
    response = aclient.get("/me")
    assert response.status_code == status.HTTP_200_OK

    json = response.json()
    assert "users" in json

    first_user = json["users"][0]

    # now test qr code, pdf and pkpass endpoints with the dl_access_token

    token = first_user["token"]

    for x, content_type in [
        ("qr-code.png", "image/png"),
        ("membership-card.pdf", "application/pdf"),
        ("membership-card.pkpass", "application/vnd.apple.pkpass"),
    ]:
        response2 = aclient.get(f"/{token}/{x}")
        assert response2.status_code == status.HTTP_200_OK
        assert content_type == response2.headers["content-type"]
