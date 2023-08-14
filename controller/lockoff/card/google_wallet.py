import typing
from datetime import datetime
from types import TracebackType

import httpx
from dateutil.relativedelta import relativedelta
from google.auth import crypt, jwt
from google.oauth2.service_account import Credentials

from ..config import settings

U = typing.TypeVar("U", bound="GooglePass")


class GoogleAuth(httpx.Auth):
    requires_response_body = True

    def __init__(self):
        self.credentials = Credentials.from_service_account_file(
            filename=settings.google_service_account,
            always_use_jwt_access=True,
            scopes=["https://www.googleapis.com/auth/wallet_object.issuer"],
        )
        print(f"scopes: {self.credentials._scopes}")
        self.credentials._create_self_signed_jwt(audience=None)
        print(f"expired {self.credentials.expired}")
        self.credentials.refresh(request=None)

    def auth_flow(self, request: httpx.Request):
        if self.credentials.expired:
            self.credentials.refresh(request=None)
        self.credentials.apply(request.headers, self.credentials.token)
        yield request


class GooglePass:
    def __init__(self):
        self.credentials = Credentials.from_service_account_file(
            filename=settings.google_service_account
        )
        self.signer = crypt.RSASigner.from_service_account_file(
            filename=settings.google_service_account
        )

        auth = GoogleAuth()

        self.client = httpx.AsyncClient(
            auth=auth,
            base_url="https://walletobjects.googleapis.com/walletobjects/v1",
        )

    async def expire_pass(self, pass_id: str):
        url = f"/genericObject/{self.issuer_id}.{pass_id}"
        patch_body = {"state": "EXPIRED"}
        response = await self.client.patch(url, json=patch_body)
        return response.status_code == 200

    async def patch_pass(self, pass_id: str, patch: dict):
        url = f"/genericObject/{settings.google_issuer_id}.{pass_id}"
        response = await self.client.patch(url, json=patch)
        return response.status_code == 200

    def _generate_generic_class(self):
        new_class = {
            "id": f"{settings.google_issuer_id}.membercard",
            "linksModuleData": {
                "uris": [
                    {
                        "uri": "https://nkk.klub-modul.dk/default.aspx",
                        "description": "Link module URI description",
                        "id": "LINK_TO_NKK",
                    },
                ]
            },
            "callbackOptions": {
                "url": "https://lockoff-api.gnerd.dk/googlepass/callback"
            },
            "multipleDevicesAndHoldersAllowedStatus": "ONE_USER_ALL_DEVICES",
            "ViewUnlockRequirement": "UNLOCK_NOT_REQUIRED",
        }
        return new_class

    def _generate_generic_object(
        self,
        pass_id: str,
        name: str,
        level: str,
        expires: datetime,
        qr_code_data: str,
        totp_key: str,
        expires_delta: relativedelta(days=15),
    ):
        now = datetime.now(tz=settings.tz)
        new_object = {
            "id": f"{settings.google_issuer_id}.{pass_id}",
            "classId": f"{settings.google_issuer_id}.membercard",
            "state": "ACTIVE",
            "genericType": "GENERIC_GYM_MEMBERSHIP",
            "passConstraints": {"screenshotEligibility": "INELIGIBLE"},
            # "TimeInterval": {
            #     "start": now.isoformat(timespec="seconds"),
            #     "end": (expires + expires_delta).isoformat(timespec="seconds"),
            # },
            "cardTitle": {
                "defaultValue": {
                    "language": "en-US",
                    "value": settings.apple_pass_logo_text,
                }
            },
            # "subheader": {"defaultValue": {"langugae": "en-US", "value": "Name"}},
            "header": {"defaultValue": {"language": "en-US", "value": name}},
            "textModulesData": [
                {
                    "header": "Level",
                    "body": level,
                    "id": "TEXT_NAME",
                },
                {
                    "header": "Expires",
                    "body": f"{expires:%Y-%m-%d}",
                    "id": "TEXT_EXPIRES",
                },
            ],
            # "rotatingBarcode": {
            #     "type": "QR_CODE",
            #     "valuePattern": f"{qr_code_data}{{totp_value_0}}",
            #     "totpDetails": {
            #         "algorithm": "TOTP_SHA1",
            #         "periodMillis": "30000",
            #         "parameters": [
            #             {
            #                 "key": totp_key,
            #                 "valueLength": "8",
            #             }
            #         ],
            #     },
            # },
            "barcode": {"type": "QR_CODE", "value": qr_code_data},
            "hexBackgroundColor": "#fff",
            "logo": {
                "sourceUri": {"uri": "https://lockoff.nkk.dk/apple-touch-icon.png"},
                "contentDescription": {
                    "defaultValue": {"language": "en-US", "value": "NKK logo"}
                },
            },
        }
        return new_object

    async def create_object(
        self,
        pass_id: str,
        name: str,
        level: str,
        expires: datetime,
        qr_code_data: str,
        totp_key: str,
    ) -> bool:
        url = f"/genericObject/{settings.google_issuer_id}.{pass_id}"
        # check if exists?
        response = await self.client.get(url)
        if response.status_code == httpx._status_codes.codes.OK:
            return True
        # create it
        response = await self.client.post(
            url,
            json=self._generate_generic_object(
                pass_id=pass_id,
                name=name,
                level=level,
                expires=expires,
                qr_code_data=qr_code_data,
                totp_key=totp_key,
            ),
        )
        print(response.json())
        return response.status_code == 200

    async def create_pass(
        self,
        pass_id: str,
        name: str,
        level: str,
        expires: datetime,
        qr_code_data: str,
        totp_key: str,
    ):
        await self.create_object(
            pass_id=pass_id,
            name=name,
            level=level,
            expires=expires,
            qr_code_data=qr_code_data,
            totp_key=totp_key,
        )
        claims = {
            "iss": self.credentials.service_account_email,
            "aud": "google",
            "origins": ["lockoff.nkk.dk"],
            "typ": "savetowallet",
            "payload": {
                "genericObjects": [
                    {
                        "id": pass_id,
                        "classId": f"{settings.google_issuer_id}.membercard",
                    }
                ]
            },
        }
        token = jwt.encode(self.signer, claims).decode("utf-8")
        return f"https://pay.google.com/gp/v/save/{token}"

    async def __aenter__(self: U) -> U:
        return self

    async def __aexit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]] = None,
        exc_value: typing.Optional[BaseException] = None,
        traceback: typing.Optional[TracebackType] = None,
    ) -> None:
        await self.client.aclose()
