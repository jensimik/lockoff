import pytest
from fastapi import status, BackgroundTasks
from fastapi.testclient import TestClient


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
    mobile_send_mock = mocker.patch("lockoff.routers.auth.send_mobile")
    spy = mocker.spy(BackgroundTasks, "add_task")
    data = {"username": mobile, "username_type": "mobile"}
    response = client.post("/request-totp", json=data)

    assert response.status_code == status.HTTP_200_OK
    spy.assert_called_with(mocker.ANY, mobile=mobile, message=mocker.ANY)
