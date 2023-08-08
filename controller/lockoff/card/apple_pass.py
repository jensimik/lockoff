import hashlib
import io
import json
import logging
import pathlib
import zipfile
from datetime import datetime

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization import pkcs7

from ..config import settings

module_directory = pathlib.Path(__file__).resolve().parent
log = logging.getLogger(__name__)


def _read_file_bytes(path):
    with open(path, "rb") as f:
        data = f.read()
    return data


class ApplePass:
    FILES = {
        "logo.png": _read_file_bytes(module_directory / "logo.png"),
        "icon.png": _read_file_bytes(module_directory / "logo.png"),
        "icon@2x.png": _read_file_bytes(module_directory / "logo.png"),
    }
    if settings.key:
        CERT = x509.load_pem_x509_certificate(settings.certificate)
        PRIV_KEY = serialization.load_pem_private_key(
            settings.key, password=settings.certificate_password
        )
        WWDR_CERT = x509.load_pem_x509_certificate(settings.wwdr_certificate)
    OPTIONS = [pkcs7.PKCS7Options.DetachedSignature]

    @classmethod
    def create(
        self,
        user_id: int,
        name: str,
        level: str,
        expires: datetime,
        qr_code_data: str,
        update_auth_token: str,
    ):
        zip_file = io.BytesIO()
        pass_json = json.dumps(
            {
                "logoText": settings.apple_pass_logo_text,
                "organizationName": settings.apple_pass_organization_name,
                "passTypeIdentifier": settings.apple_pass_pass_type_identifier,
                "serialNumber": f"{settings.current_season}{user_id}",
                "suppressStripShine": False,
                "teamIdentifier": settings.apple_pass_team_identifier,
                "description": settings.apple_pass_description,
                "expirationDate": f"{expires:%Y-%m-%d}T{expires:%H:%M:%S}Z",
                "sharingProhibited": True,
                "formatVersion": 1,
                "webServiceURL": settings.apple_pass_web_service_url,
                "authenticationToken": update_auth_token,
                "barcodes": [
                    {
                        "format": "PKBarcodeFormatQR",
                        "message": qr_code_data,
                        "messageEncoding": "iso-8859-1",
                    }
                ],
                "locations": [
                    {
                        "altitude": 0.0,
                        "latitude": settings.apple_pass_latitude,
                        "longitude": settings.apple_pass_longitude,
                        "relevantText": settings.apple_pass_relevant_text,
                    }
                ],
                "maxDistance": 20,
                "beacons": [
                    {
                        "proximityUUID": settings.apple_pass_proximity_uuid,
                        "major": 0,
                        "minor": 0,
                        "relevantText": settings.apple_pass_relevant_text,
                    }
                ],
                "generic": {
                    "backFields": [
                        {
                            "changeMessage": "",
                            "key": "support",
                            "label": "Support contact",
                            "textAlignment": "PKTextAlignmentLeft",
                            "value": "sekretariat@nkk.dk",
                        },
                        {
                            "changeMessage": "",
                            "key": "website",
                            "label": "Website",
                            "textAlignment": "PKTextAlignmentLeft",
                            "value": "https://nkk.klub-modul.dk",
                        },
                    ],
                    "primaryFields": [
                        {
                            "changeMessage": "",
                            "key": "name",
                            "label": "Name",
                            "textAlignment": "PKTextAlignmentLeft",
                            "value": name,
                        }
                    ],
                    "secondaryFields": [
                        {
                            "changeMessage": "",
                            "key": "membership",
                            "label": "Membership",
                            "textAlignment": "PKTextAlignmentLeft",
                            "value": level,
                        },
                        {
                            "changeMessage": "",
                            "key": "expire",
                            "label": "Expires",
                            "textAlignment": "PKTextAlignmentLeft",
                            "value": f"{expires:%Y-%m-%d}T{expires:%H:%M:%S}Z",
                            "timeStyle": "PKDateStyleNone",
                            "dateStyle": "PKDateStyleShort",
                        },
                    ],
                },
            }
        )
        # create manifest
        _hashes = {"pass.json": hashlib.sha1(pass_json.encode("utf-8")).hexdigest()}
        for filename, filedata in self.FILES.items():
            _hashes[filename] = hashlib.sha1(filedata).hexdigest()
        manifest = json.dumps(_hashes)
        # create signature
        signature = (
            pkcs7.PKCS7SignatureBuilder()
            .set_data(manifest.encode("UTF-8"))
            .add_signer(self.CERT, self.PRIV_KEY, hashes.SHA1())
            .add_certificate(self.WWDR_CERT)
            .sign(serialization.Encoding.DER, self.OPTIONS)
        )
        # create pkpass zipfile
        with zipfile.ZipFile(zip_file, "w") as zf:
            zf.writestr("signature", signature)
            zf.writestr("manifest.json", manifest)
            zf.writestr("pass.json", pass_json)
            for filename, filedata in self.FILES.items():
                zf.writestr(filename, filedata)
        return zip_file


# if __name__ == "__main__":
#     pkpass = ApplePass.create(
#         user_id=100,
#         name="Test Testersen",
#         level="Normal",
#         expires=datetime(2024, 1, 1, 12, 0, 0),
#         barcode_data="test1234",
#     )
