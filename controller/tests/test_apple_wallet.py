import zipfile
from datetime import datetime, timedelta

import pytest
from lockoff.card import AppleNotifier, ApplePass
from lockoff.config import settings


def test_basic_pass():
    soon = datetime.now(tz=settings.tz) + timedelta(hours=1)
    cert = ApplePass.create(
        serial="2023358",
        name="Test Testersen",
        level="Normal",
        expires=soon,
        qr_code_data="TEST_QR_CODE",
        update_auth_token="UPDATE_AUTH_TOKEN",
    )
    with zipfile.ZipFile(cert, "r") as zf:
        assert zf.testzip() == None
        files = zf.namelist()
        for required_file in [
            "signature",
            "manifest.json",
            "pass.json",
            "logo.png",
            "icon.png",
            "icon@2x.png",
        ]:
            assert required_file in files


@pytest.mark.asyncio
async def test_basic_notifier(httpx_mock):
    push_token = "test-token"
    httpx_mock.add_response(
        method="POST", url=f"https://api.push.apple.com:443/3/device/{push_token}"
    )
    async with AppleNotifier() as notifier:
        await notifier.notify_update(push_token=push_token)
