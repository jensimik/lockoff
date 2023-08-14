import httpx
import base64

GOOGLE_PUBLIC_KEY_URL = "https://pay.google.com/gp/m/issuer/keys"
GOOGLE_SENDER_ID = "GooglePayPasses"
EXPIRATION_INTERVAL = 3600  # // check 1 hour before key expires
PROTOCOL_VERSION = "ECv2SigningOnly"


class PaymentMethodTokenRecipient:
    def __init__(self):
        self.google_public_keys = []
        self.public_key_expiration = None

    async def _refresh_public_keys(self):
        response = await httpx.get(GOOGLE_PUBLIC_KEY_URL)
        data = response.json()
        for key in data["keys"]:
            keyvalue = base64.b64decode(key["keyValue"])

        await self._fetch_public_keys()

    async def get_public_key(self, key):
        pass


a = {
    "signature": "MEQCICNRcl4MLW0d5hcFi/h2OijYW2boEU5IS9I37wOJO0v8AiB0et62sYYI00gO4QeXS0ZlLCjpkLqvLk4SsCx6f5jfyQ==",
    "intermediateSigningKey": {
        "signedKey": '{"keyValue":"MFkwEwYHKoZIzj0CAQYIKoZIzj0DAQcDQgAEIQab9kGfAsSgBnFPMXGXlOpL7WhWqCYC/FjS70H4bhp/qbyaBIMR3R98cEylL4jCJiVFQ8dtltpr3NCzq/iTgg\\u003d\\u003d","keyExpiration":"1692688147000"}',
        "signatures": [
            "MEYCIQCOhXCleCo64oKagwmJWUGmvODW5iAeZzQAocRcMiceIAIhAJENpGpyKYgSNybrA68pLFFsGTNFiQ4i4qL0bRnpgIDd"
        ],
    },
    "protocolVersion": "ECv2SigningOnly",
    "signedMessage": '{"classId":"3388000000022211970.membercard","objectId":"3388000000022211970.20233587","eventType":"save","expTimeMillis":1692032148434,"count":1,"nonce":"22729f93-640a-40fc-9679-02d6fab107a0"}',
}

if __name__ == "__main__":
    print("hej")
