import pytest
from lockoff.klubmodul import KMClient
from lockoff.config import settings


@pytest.mark.asyncio
async def test_klubmodul_send_sms(httpx_mock):
    # login
    httpx_mock.add_response(
        method="POST", url=f"{settings.klubmodul_base_url}/default.aspx"
    )
    # send sms
    httpx_mock.add_response(
        method="POST",
        url=f"{settings.klubmodul_base_url}/Adminv2/NewsMail/__Create",
        json={"savedId": 100},
    )
    # remove sms
    httpx_mock.add_response(
        method="DELETE",
        url=f"{settings.klubmodul_base_url}/Adminv2/Newsmail/__Delete",
    )

    async with KMClient() as km:
        await km.send_sms(user_id=1, message="test message", delete_delay=0)


@pytest.mark.asyncio
async def test_klubmodul_send_email(httpx_mock):
    # login
    httpx_mock.add_response(
        method="POST", url=f"{settings.klubmodul_base_url}/default.aspx"
    )
    # send sms
    httpx_mock.add_response(
        method="POST",
        url=f"{settings.klubmodul_base_url}/Adminv2/NewsMail/__Create",
        json={"savedId": 100},
    )
    # remove sms
    httpx_mock.add_response(
        method="DELETE",
        url=f"{settings.klubmodul_base_url}/Adminv2/Newsmail/__Delete",
    )

    async with KMClient() as km:
        await km.send_email(
            user_id=1, subject="test-subject", message="test message", delete_delay=0
        )
