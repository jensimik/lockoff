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
        self.credentials._create_self_signed_jwt()

    def auth_flow(self, request: httpx.Request):
        if self.credentials.expired:
            self.credentials._jwt_credentials.refresh()
        self.credentials._jwt_credentials.apply(request.headers)
        yield request


class GooglePass:
    def __init__(self):
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

    def _generate_class(self):
        new_class = {
            "id": f"{self.issuer_id}.membercard",
            # "callback": {"url": "https://lockoff-api.gnerd.dk/"},
        }

    def _generate_generic_object(
        self, pass_id: str, name: str, level: str, expires: str, qr_code_data: str
    ):
        new_object = {
            "id": f"{self.issuer_id}.{pass_id}",
            "classId": f"{self.issuer_id}.membercard",
            "state": "ACTIVE",
            "heroImage": {
                "sourceUri": {
                    "uri": "https://farm4.staticflickr.com/3723/11177041115_6e6a3b6f49_o.jpg"
                },
                "contentDescription": {
                    "defaultValue": {
                        "language": "en-US",
                        "value": "Hero image description",
                    }
                },
            },
            "textModulesData": [
                {
                    "header": "Text module header",
                    "body": "Text module body",
                    "id": "TEXT_MODULE_ID",
                }
            ],
            "linksModuleData": {
                "uris": [
                    {
                        "uri": "http://maps.google.com/",
                        "description": "Link module URI description",
                        "id": "LINK_MODULE_URI_ID",
                    },
                    {
                        "uri": "tel:6505555555",
                        "description": "Link module tel description",
                        "id": "LINK_MODULE_TEL_ID",
                    },
                ]
            },
            "imageModulesData": [
                {
                    "mainImage": {
                        "sourceUri": {
                            "uri": "http://farm4.staticflickr.com/3738/12440799783_3dc3c20606_b.jpg"
                        },
                        "contentDescription": {
                            "defaultValue": {
                                "language": "en-US",
                                "value": "Image module description",
                            }
                        },
                    },
                    "id": "IMAGE_MODULE_ID",
                }
            ],
            "barcode": {"type": "QR_CODE", "value": qr_code_data},
            "cardTitle": {
                "defaultValue": {"language": "en-US", "value": "Generic card title"}
            },
            "header": {
                "defaultValue": {"language": "en-US", "value": "Generic header"}
            },
            "hexBackgroundColor": "#4285f4",
            "logo": {
                "sourceUri": {
                    "uri": "https://storage.googleapis.com/wallet-lab-tools-codelab-artifacts-public/pass_google_logo.jpg"
                },
                "contentDescription": {
                    "defaultValue": {"language": "en-US", "value": "Generic card logo"}
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
