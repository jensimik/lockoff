import pytest
from lockoff.card import GooglePass, GPassStatus
from lockoff.config import settings
from datetime import datetime, timedelta


@pytest.mark.asyncio
async def test_basic_update(httpx_mock):
    pass_id = "2023358"
    url = f"https://walletobjects.googleapis.com/walletobjects/v1/genericObject/{settings.google_issuer_id}.{pass_id}"
    httpx_mock.add_response(method="GET", url=url, status_code=200, json={})
    httpx_mock.add_response(method="PUT", url=url, status_code=200, json={})

    expires = datetime.now(tz=settings.tz) + timedelta(hours=2)
    async with GooglePass() as gp:
        await gp.create_pass(
            pass_id=pass_id,
            name="test testersen",
            level="normal",
            expires=expires,
            qr_code_data="TEST_QR_CODE",
            totp_key="TOTP_KEY",
        )


@pytest.mark.asyncio
async def test_basic_insert(httpx_mock):
    pass_id = "2023358"
    url = f"https://walletobjects.googleapis.com/walletobjects/v1/genericObject/{settings.google_issuer_id}.{pass_id}"
    httpx_mock.add_response(method="GET", url=url, status_code=404)
    httpx_mock.add_response(
        method="POST",
        url="https://walletobjects.googleapis.com/walletobjects/v1/genericObject",
        status_code=200,
        json={},
    )

    expires = datetime.now(tz=settings.tz) + timedelta(hours=2)
    async with GooglePass() as gp:
        await gp.create_pass(
            pass_id=pass_id,
            name="test testersen",
            level="normal",
            expires=expires,
            qr_code_data="TEST_QR_CODE",
            totp_key="TOTP_KEY",
        )


@pytest.mark.asyncio
async def test_basic_create_class_insert(httpx_mock):
    url = f"https://walletobjects.googleapis.com/walletobjects/v1/genericClass/{settings.google_issuer_id}.membercard"
    httpx_mock.add_response(method="GET", url=url, status_code=404)
    httpx_mock.add_response(
        method="POST",
        url="https://walletobjects.googleapis.com/walletobjects/v1/genericClass",
        status_code=200,
        json={},
    )

    async with GooglePass() as gp:
        await gp.create_class()


@pytest.mark.asyncio
async def test_basic_create_class_update(httpx_mock):
    url = f"https://walletobjects.googleapis.com/walletobjects/v1/genericClass/{settings.google_issuer_id}.membercard"
    httpx_mock.add_response(method="GET", url=url, status_code=200)
    httpx_mock.add_response(
        method="PUT",
        url=url,
        status_code=200,
        json={},
    )

    async with GooglePass() as gp:
        await gp.create_class()
