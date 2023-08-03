import pytest
from fastapi import BackgroundTasks, status
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


def test_request_totp_mobile(mocker, client: TestClient):
    mobile = "10001000"
    mock = mocker.patch("fastapi.BackgroundTasks.add_task")
    data = {"username": mobile, "username_type": "mobile"}
    response = client.post("/request-totp", json=data)

    assert response.status_code == status.HTTP_200_OK
    assert mock.called_once()
    assert mock.called_with(mocker.ANY, send_mobile, mobile=mobile, message=mocker.ANY)


def test_request_totp_email(mocker, client: TestClient):
    email = "test1@test.dk"
    mock = mocker.patch("fastapi.BackgroundTasks.add_task")
    data = {"username": email, "username_type": "email"}
    response = client.post("/request-totp", json=data)

    assert response.status_code == status.HTTP_200_OK
    assert mock.called_once()
    assert mock.called_with(mocker.ANY, send_email, email=email, message=mocker.ANY)
