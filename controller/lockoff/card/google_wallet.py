import json
import os
import typing
import uuid
from types import TracebackType

import httpx
from google.auth import crypt, jwt
from google.oauth2.service_account import Credentials

from ..config import settings

U = typing.TypeVar("U", bound="GooglePass")


class GoogleAuth(httpx.Auth):
    requires_response_body = True

    def __init__(self):
        self.credentials = Credentials.from_service_account_file(
            filename=settings.google_service_account,
            scopes=["https://www.googleapis.com/auth/wallet_object.issuer"],
        )
        self.credentials._always_use_jwt_access = True
        self.credentials._create_self_signed_jwt(audience=None)

    def auth_flow(self, request: httpx.Request):
        if self.credentials.expired:
            self.credentials._jwt_credentials.refresh()
        self.credentials._jwt_credentials.apply(request.headers)
        yield request


class GooglePass:
    def __init__(self):
        self.credentials = Credentials.from_service_account_file(
            filename=settings.google_service_account
        )
        self.signer = crypt.RSASigner.from_service_account_file(
            filename=settings.google_service_account
        )
        self.issuer_id = settings.google_issuer_id
        self.base_url = "https://walletobjects.googleapis.com/walletobjects/v1"
        self.object_url = "/genericObject"

        auth = GoogleAuth()

        self.client = httpx.AsyncClient(
            auth=auth,
            base_url=self.base_url,
        )

    async def expire_pass(self, pass_id: str):
        url = f"/genericObject/{self.issuer_id}.{pass_id}"
        patch_body = {"state": "EXPIRED"}
        response = await self.client.patch(url, json=patch_body)
        return response.status_code == 200

    async def patch_pass(self, pass_id: str, patch: dict):
        url = f"/genericObject/{self.issuer_id}.{pass_id}"
        response = await self.client.patch(url, json=patch)
        return response.status_code == 200

    def _generate_generic_class(self):
        new_class = {
            "id": f"{self.issuer_id}.membercard",
            # "callback": {"url": "https://lockoff-api.gnerd.dk/"},
        }
        return new_class

    def _generate_generic_object(
        self, pass_id: str, name: str, level: str, expires: str, qr_code_data: str
    ):
        new_object = {
            "id": f"{self.issuer_id}.{pass_id}",
            "classId": f"{self.issuer_id}.membercard",
            "state": "ACTIVE",
            "genericType": "GENERIC_GYM_MEMBERSHIP",
            "cardTitle": {
                "defaultValue": {
                    "language": "en-US",
                    "value": settings.apple_pass_logo_text,
                }
            },
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
            "linksModuleData": {
                "uris": [
                    {
                        "uri": "https://nkk.klub-modul.dk/default.aspx",
                        "description": "Link module URI description",
                        "id": "LINK_TO_NKK",
                    },
                ]
            },
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

    def create_pass(
        self,
        pass_id: str,
        name: str,
        level: str,
        expires: str,
        qr_code_data: str,
    ):
        claims = {
            "iss": self.credentials.service_account_email,
            "aud": "google",
            "origins": ["lockoff.nkk.dk"],
            "typ": "savetowallet",
            "payload": {
                "genericClasses": [self._generate_generic_class()],
                "genericObjects": [
                    self._generate_generic_object(
                        pass_id=pass_id,
                        name=name,
                        level=level,
                        expires=expires,
                        qr_code_data=qr_code_data,
                    )
                ],
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
