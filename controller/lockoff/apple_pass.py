import hashlib
import io
import json
import zipfile
from datetime import datetime

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization import pkcs7

from .config import settings


def _read_file_bytes(path):
    with open(path, "rb") as f:
        data = f.read()
    return data


class ApplePass:
    FILES = {
        "logo.png": _read_file_bytes("logo.png"),
        "icon.png": _read_file_bytes("logo.png"),
        "icon@2x.png": _read_file_bytes("logo.png"),
    }
    CERT = x509.load_pem_x509_certificate(settings.certificate)
    PRIV_KEY = serialization.load_pem_private_key(
        settings.key, password=settings.certificate_password
    )
    WWDR_CERT = x509.load_pem_x509_certificate(settings.wwdr_certificate)
    OPTIONS = [pkcs7.PKCS7Options.DetachedSignature]

    @classmethod
    def create(
        self,
        zip_file: io.BufferedIOBase,
        user_id: int,
        name: str,
        level: str,
        expires: datetime,
        barcode_data: str,
    ):
        pass_json = json.dumps(
            {
                "logoText": "Nørrebro klatreklub",
                "organizationName": "Jens Davidsen",
                "passTypeIdentifier": "pass.dk.nkk.lockoff",
                "serialNumber": f"{expires:%Y}{user_id}",
                "suppressStripShine": False,
                "teamIdentifier": "LLFSXFW7XK",
                "description": "Nørrebro klatreklub",
                "expirationDate": f"{expires:%Y-%m-%d}T{expires:%H:%M:%S}Z",
                "formatVersion": 1,
                "barcodes": [
                    {
                        "format": "PKBarcodeFormatQR",
                        "message": barcode_data,
                        "messageEncoding": "iso-8859-1",
                    }
                ],
                "locations": [
                    {
                        "altitude": 0.0,
                        "latitude": 55.69942723771949,
                        "longitude": 12.543439832016006,
                        "relevantText": "lets climb! 🐒",
                    }
                ],
                # "ibeacons": [
                #     {
                #         "proximityUUID": None,
                #         "major": None,
                #         "minor": None,
                #         "relevantText": "",
                #     }
                # ],
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


# if __name__ == "__main__":
#    with open("test2.pkpass", "wb") as f:
#        p = ApplePass.create(
#            zip_file=f,
#            user_id=100,
#            name="Jens Davidsen",
#            level="Normal",
#            expires=datetime(2024, 1, 1, 12, 0, 0),
#            barcode_data="test1234",
#        )
