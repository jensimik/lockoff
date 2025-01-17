import json

import pyotp
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from lockoff.access_token import (
    TokenType,
    generate_access_token,
    generate_dl_admin_token,
)
from lockoff.config import settings
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
        ("/admin/daytickets/wrongtoken/qr-code.png", 400),
        ("/admin/system-status", 401),
    ),
)
def test_endpoint_generic(url, expected_status_code, client: TestClient):
    response = client.get(url)
    assert response.status_code == expected_status_code


@pytest.mark.parametrize(
    ["url", "expected_status_code"],
    (
        ("/admin/daytickets/wrongtoken/qr-code.png", 400),
        ("/admin/system-status", 401),
    ),
)
def test_endpoint_generic_admin(url, expected_status_code, a0client: TestClient):
    response = a0client.get(url)
    assert response.status_code == expected_status_code


def test_bad_jwt(client: TestClient):
    response = client.get("/me", headers={"Authorization": "bearer badjwt"})
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.parametrize(
    ["user_id", "ok"],
    (
        (0, True),  # normal user
        (5, True),  # morning user
        (9, False),  # inactive user
        (1000, False),  # unknown user
    ),
)
def test_request_totp_mobile(user_id, ok, mocker, client: TestClient):
    mobile = f"1000100{user_id}"
    mock = mocker.patch("fastapi.BackgroundTasks.add_task")
    data = {"username": mobile, "username_type": "mobile"}
    response = client.post("/request-totp", json=data)

    if ok:
        assert response.status_code == status.HTTP_200_OK
        mock.assert_called_once()
        mock.assert_called_with(send_mobile, user_id=user_id, message=mocker.ANY)
    else:
        assert response.status_code == status.HTTP_404_NOT_FOUND
        mock.assert_not_called()


@pytest.mark.parametrize(
    ["user_id", "ok"],
    (
        (0, True),  # normal user
        (5, True),  # morning user
        (9, False),  # inactive user
        (1000, False),  # unknown user
    ),
)
def test_request_totp_email(user_id, ok, mocker, client: TestClient):
    email = f"test{user_id}@test.dk"
    mock = mocker.patch("fastapi.BackgroundTasks.add_task")
    data = {"username": email, "username_type": "email"}
    response = client.post("/request-totp", json=data)

    if ok:
        assert response.status_code == status.HTTP_200_OK
        mock.assert_called_once()
        mock.assert_called_with(send_email, user_id=user_id, message=mocker.ANY)
    else:
        assert response.status_code == status.HTTP_404_NOT_FOUND
        mock.assert_not_called()


@pytest.mark.asyncio
async def test_send_sms(mocker):
    km_login = mocker.patch("lockoff.routers.auth.KMClient._km_login")
    km_send_sms = mocker.patch("lockoff.routers.auth.KMClient.send_sms")
    await send_mobile(user_id=1, message="test")
    km_login.assert_awaited_once()
    km_send_sms.assert_awaited_once()


@pytest.mark.asyncio
async def test_send_email(mocker):
    km_login = mocker.patch("lockoff.routers.auth.KMClient._km_login")
    km_send_email = mocker.patch("lockoff.routers.auth.KMClient.send_email")
    await send_email(user_id=1, message="test")
    km_login.assert_awaited_once()
    km_send_email.assert_awaited_once()


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


def test_google_wallet_callback(client: TestClient):
    data = {"signedMessage": json.dumps({"objectId": "12345.1", "eventType": "save"})}
    response = client.post("/google-wallet/callback", json=data)
    assert response.status_code == status.HTTP_200_OK

    data = {"signedMessage": json.dumps({"objectId": "12345.1", "eventType": "del"})}
    response = client.post("/google-wallet/callback", json=data)
    assert response.status_code == status.HTTP_200_OK


# def test_apple_wallet_callbacks(a2client: TestClient):
#     response = a2client.post("/apple-wallet/v1/log", json={"logs": ["test1", "test2"]})
#     assert response.status_code == status.HTTP_200_OK

#     device_library_identifier = "test-device"
#     pass_type_identifier = "pass-type-id"
#     serial_number = "20241"
#     data = {"pushToken": "push-token", "pushServiceUrl": "https://localhost/something"}
#     response = a2client.post(
#         f"/apple-wallet/v1/devices/{device_library_identifier}/registrations/{pass_type_identifier}/{serial_number}",
#         json=data,
#     )
#     assert response.status_code == status.HTTP_200_OK

#     response = a2client.get(
#         f"/apple-wallet/v1/devices/{device_library_identifier}/registrations/{pass_type_identifier}"
#     )
#     assert response.status_code == status.HTTP_200_OK

#     last_updated = response.json()["lastUpdated"]

#     response = a2client.get(
#         f"/apple-wallet/v1/devices/{device_library_identifier}/registrations/{pass_type_identifier}?passesUpdatedSince={last_updated}"
#     )
#     assert response.status_code == status.HTTP_204_NO_CONTENT

#     response = a2client.get(
#         f"/apple-wallet/v1/passes/{pass_type_identifier}/{serial_number}"
#     )
#     assert response.status_code == status.HTTP_200_OK

#     response = a2client.delete(
#         f"/apple-wallet/v1/devices/{device_library_identifier}/registrations/{pass_type_identifier}/{serial_number}"
#     )
#     assert response.status_code == status.HTTP_200_OK


def test_me(a0client: TestClient, mocker):
    response = a0client.get("/me")
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
        response = a0client.get(f"/{token}/{x}")
        assert response.status_code == status.HTTP_200_OK
        assert content_type == response.headers["content-type"]

    async def _create_pass(*args, **kwargs):
        return "http://localhost/jwt-redirect-url"

    mocker.patch("lockoff.routers.card.GooglePass.create_pass", _create_pass)
    response = a0client.get(f"/{token}/membership-card", follow_redirects=False)
    assert response.status_code == status.HTTP_307_TEMPORARY_REDIRECT

    # normal user do not have access to admin
    response = a0client.get("/admin/system-status")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_admin(a1client: TestClient, mocker):
    # system-status
    response = a1client.get("/admin/system-status")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["digital_issued"] == 2
    assert data["print_issued"] == 1
    assert data["total_issued"] == 2

    # generate daytickets
    response = a1client.post("/admin/daytickets", json={"pages_to_print": 1})
    assert response.status_code == status.HTTP_200_OK

    # check qr-codes on the dayticket print
    dl_token = generate_dl_admin_token(user_id=1)
    response = a1client.get(f"/admin/daytickets/{dl_token}/qr-code.png")
    assert response.status_code == status.HTTP_200_OK

    # check token
    token = generate_access_token(user_id=1).decode()
    response = a1client.post("/admin/check-token", json={"token": token})
    assert response.status_code == status.HTTP_200_OK

    # check dayticket token not activated yet
    token = generate_access_token(user_id=1, token_type=TokenType.DAY_TICKET).decode()
    response = a1client.post("/admin/check-token", json={"token": token})
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # check dayticket not found
    token = generate_access_token(
        user_id=1000, token_type=TokenType.DAY_TICKET
    ).decode()
    response = a1client.post("/admin/check-token", json={"token": token})
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # check expired dayticket
    token = generate_access_token(user_id=2, token_type=TokenType.DAY_TICKET).decode()
    response = a1client.post("/admin/check-token", json={"token": token})
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # check valid dayticket
    token = generate_access_token(user_id=3, token_type=TokenType.DAY_TICKET).decode()
    response = a1client.post("/admin/check-token", json={"token": token})
    assert response.status_code == status.HTTP_200_OK

    # check wrong token
    modify = "A" if token[-1] != "A" else "B"
    token = token[:-1] + modify
    response = a1client.post("/admin/check-token", json={"token": token})
    assert response.status_code == status.HTTP_400_BAD_REQUEST

    # test force-resync-klubmodul
    refresh = mocker.patch("lockoff.routers.admin.refresh")
    response = a1client.post("/admin/klubmodul-force-resync")
    assert response.status_code == status.HTTP_200_OK
    refresh.assert_awaited_once()

    response = a1client.get("/admin/log-raw.json")
    assert response.status_code == status.HTTP_200_OK

    response = a1client.get("/admin/log-unique-daily.json")
    assert response.status_code == status.HTTP_200_OK

    response = a1client.get("/admin/log-user-freq.json")
    assert response.status_code == status.HTTP_200_OK
