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


@pytest.mark.asyncio
async def test_klubmodul_get_members(httpx_mock):
    # login
    httpx_mock.add_response(
        method="POST", url=f"{settings.klubmodul_base_url}/default.aspx"
    )
    # get csv
    httpx_mock.add_response(
        method="POST",
        url=f"{settings.klubmodul_base_url}/Adminv2/SearchProfile/ExportCsv",
        text="""Id;Fornavn;Efternavn;Email;Mobil;NogetAndet;Hold
1;F1;E;f1@e.dk;80808081;adsf;1
2;F2;E;f2@e.dk;80808082;asdf;2
3;F3;E;f3@e.dk;80808083;asdf;1
4;F5;E;f5@e.dk;80808085;asdf;
5;F4;E;f4@e.dk;80808084;asdf;2
""",
    )

    async with KMClient() as km:
        i = 0
        async for user_id, name, member_type, email, mobile in km.get_members():
            assert user_id > 0
            print(user_id)
            i += 1
        # only show 4 as user_id 4 is not a member (not in a hold)
        assert i == 4
