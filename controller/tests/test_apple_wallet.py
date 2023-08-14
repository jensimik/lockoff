from lockoff.card import ApplePass
from datetime import datetime, timedelta
from lockoff.config import settings
import zipfile


def test_basic():
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
