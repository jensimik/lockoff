import hashlib
import io
import json
import logging
import pathlib
import time
import typing
import zipfile
import uuid
from datetime import datetime
from types import TracebackType

import httpx
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.serialization import pkcs7
from jose import jwt

from ..config import settings

module_directory = pathlib.Path(__file__).resolve().parent
log = logging.getLogger(__name__)


def _read_file_bytes(path):
    with open(path, "rb") as f:
        data = f.read()
    return data


U = typing.TypeVar("U", bound="AppleNotifier")


class AppleNotifier:
    def __init__(self):
        self._auth_key = serialization.load_pem_private_key(
            settings.apn_auth_key, password=None
        )

    async def __aenter__(self: U) -> U:
        iat = int(time.time())
        ALG = "ES256"
        token = jwt.encode(
            {"iss": settings.apple_pass_team_identifier, "iat": iat},
            self._auth_key,
            algorithm=ALG,
            headers={"alg": ALG, "kid": settings.apn_key_id},
        )
        limits = httpx.Limits(max_connections=1, max_keepalive_connections=0)
        self.client = httpx.AsyncClient(
            base_url="https://api.push.apple.com:443",
            http2=True,
            timeout=10.0,
            limits=limits,
            headers={
                "Authorization": f"bearer {token}",
                "Content-Type": "application/json; charset=utf-8",
            },
        )
        return self

    async def notify_update(self, str, push_token: str) -> bool:
        try:
            headers = {
                "apns-topic": settings.apple_pass_pass_type_identifier,
                # "apns-id": uuid.uuid4().hex,
                # "apns-expiration": "{}".format(int(time.time()) + 3600),
                # "apns-push-type": "background",
            }
            response = await self.client.post(
                f"/3/device/{push_token}", headers=headers, json={}
            )
            log.info(response.status_code)
            if response.status_code != 200:
                log.info(response.json())
                log.info(response.text)
        except httpx.RequestError as ex:
            log.exception(f"failed in notify update with {ex}")
        log.info(f"notify_update status code: {response.status_code}")

    async def notify_alert(
        self, device_library_identifier: str, push_token: str
    ) -> bool:
        try:
            headers = {
                "apns-topic": settings.apple_pass_pass_type_identifier,
                "apns-id": uuid.uuid4().hex,
                "apns-expiration": "{}".format(int(time.time()) + 3600),
                "apns-push-type": "alert",
            }
            response = await self.client.post(
                f"/3/device/{push_token}", headers=headers, json={"aps": "hej med dig"}
            )
            log.info(response.status_code)
            if response.status_code != 200:
                log.info(response.json())
                log.info(response.text)
        except httpx.RequestError as ex:
            log.exception(f"failed in notify update with {ex}")
        log.info(f"notify_update status code: {response.status_code}")

    async def notify_update_passwallet(self, identifiers: list[str]) -> bool:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(
                "http://push.passwallet.net/v1/pushUpdates",
                json={
                    "passTypeID": settings.apple_pass_pass_type_identifier,
                    "pushTokens": identifiers,
                },
            )
            return response.status_code == 200

    async def notify_update_wallet_pass(self, identifiers: list[str]):
        headers = {"Authorization": settings.walletpass_token}
        async with httpx.AsyncClient(timeout=10.0, headers=headers) as client:
            response = await client.post(
                "https://walletpasses.appspot.com/api/v1/push",
                json={
                    "passTypeIdentifier": settings.apple_pass_pass_type_identifier,
                    "pushTokens": identifiers,
                },
            )
            return response.status_code == 200

    async def notify_badge(serial: str, message: str) -> bool:
        pass

    async def aclose(self) -> None:
        await self.client.aclose()

    async def __aexit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]] = None,
        exc_value: typing.Optional[BaseException] = None,
        traceback: typing.Optional[TracebackType] = None,
    ) -> None:
        await self.aclose()


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
        serial: str,
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
                "serialNumber": serial,
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
