import httpx
import pytest
from lockoff.config import settings
from lockoff.klubmodul import KlubmodulException, KMClient, klubmodul_runner, refresh


@pytest.mark.asyncio
async def test_login_timeout(httpx_mock):
    httpx_mock.add_exception(httpx.ReadTimeout("Unable to read within timeout"))
    with pytest.raises(KlubmodulException):
        async with KMClient() as _:
            pass


LOGIN_PAGE_HTML = """<html><body>
    <input type="hidden" name="__VIEWSTATE" id="__VIEWSTATE" value="abc" />
    <input type="hidden" name="__VIEWSTATEGENERATOR" id="__VIEWSTATEGENERATOR" value="def" />
    <input type="hidden" name="__EVENTVALIDATION" id="__EVENTVALIDATION" value="ghi" />
</body></html>"""


def _mock_login(httpx_mock):
    # GET login page to extract viewstate
    httpx_mock.add_response(
        method="GET",
        url=f"{settings.klubmodul_base_url}/default.aspx",
        text=LOGIN_PAGE_HTML,
    )
    # POST login — klubmodul returns 302 on success
    httpx_mock.add_response(
        method="POST",
        url=f"{settings.klubmodul_base_url}/default.aspx",
        status_code=302,
        headers={"location": "/ShowContentPage.aspx?AliasPageName=default.aspx"},
    )


@pytest.mark.asyncio
async def test_klubmodul_send_sms(httpx_mock):
    _mock_login(httpx_mock)
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
    _mock_login(httpx_mock)
    # send email
    httpx_mock.add_response(
        method="POST",
        url=f"{settings.klubmodul_base_url}/Adminv2/NewsMail/__Create",
        json={"savedId": 100},
    )
    # remove email
    httpx_mock.add_response(
        method="DELETE",
        url=f"{settings.klubmodul_base_url}/Adminv2/Newsmail/__Delete",
    )

    async with KMClient() as km:
        await km.send_email(
            user_id=1, subject="test-subject", message="test message", delete_delay=0
        )


# @pytest.mark.asyncio
# async def test_klubmodul_get_members(httpx_mock):
#     # login
#     httpx_mock.add_response(
#         method="POST", url=f"{settings.klubmodul_base_url}/default.aspx"
#     )
#     # get csv
#     httpx_mock.add_response(
#         method="POST",
#         url=f"{settings.klubmodul_base_url}/Adminv2/TeamEnrollmentList/ExportCsv",
#         text="""Id;Fornavn;Efternavn;Email;Mobil;NogetAndet;Hold
# 1;F1;E;f1@e.dk;80808081;adsf;1
# 2;F2;E;f2@e.dk;80808082;asdf;2
# 3;F3;E;f3@e.dk;80808083;asdf;1
# 4;F5;E;f5@e.dk;80808085;asdf;
# 5;F4;E;f4@e.dk;80808084;asdf;2
# """,
#         is_reusable=True,
#     )

#     async with KMClient() as km:
#         i = 0
#         async for user_id, name, member_type, email, mobile in km.get_members():
#             assert user_id > 0
#             i += 1
#         assert i == 20


# @pytest.mark.asyncio
# async def test_klubmodul_refresh(httpx_mock):
#     # login
#     httpx_mock.add_response(
#         method="POST",
#         url=f"{settings.klubmodul_base_url}/default.aspx",
#         is_reusable=True,
#     )
#     # get csv
#     httpx_mock.add_response(
#         method="POST",
#         url=f"{settings.klubmodul_base_url}/Adminv2/TeamEnrollmentList/ExportCsv",
#         text="""Id;Fornavn;Efternavn;Email;Mobil;NogetAndet;Hold
# 1;F1;E;f1@e.dk;80808081;adsf;1
# 2;F2;E;f2@e.dk;80808082;asdf;2
# 3;F3;E;f3@e.dk;80808083;asdf;1
# 4;F5;E;f5@e.dk;80808085;asdf;
# 5;F4;E;f4@e.dk;80808084;asdf;2
# """,
#         is_reusable=True,
#     )

#     await refresh()

#     # run again to verify upsert is working
#     await refresh()


@pytest.mark.asyncio
async def test_klubmodul_runner(mocker):
    refresh = mocker.patch("lockoff.klubmodul.klubmodul.refresh")
    sleep = mocker.patch("asyncio.sleep")

    await klubmodul_runner(one_time_run=True)

    sleep.assert_awaited()
    refresh.assert_awaited_once()
