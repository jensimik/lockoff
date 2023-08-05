import asyncio
import csv
import logging
import typing
from datetime import datetime
from types import TracebackType

import aiosqlite
import httpx
import pyotp

from ..config import settings
from ..misc import queries, simple_hash
from .klubmodul_login_data import data as login_data

log = logging.getLogger(__name__)

U = typing.TypeVar("U", bound="KMClient")

refresh_lock = asyncio.Lock()


class KMClient:
    def __init__(self):
        self.client = httpx.AsyncClient(
            base_url=settings.klubmodul_base_url, default_encoding="utf-8-sig"
        )

    async def _km_login(self) -> None:
        # login and session cookie is set quite ugly with viewstate data :-|
        try:
            response = await self.client.post(
                "/default.aspx",
                data=login_data,
                timeout=10.0,
            )
        except httpx.TimeoutException:
            raise KlubmodulException("failed to login due to timeout")
        if response.is_error:
            raise KlubmodulException("failed to login: " + response.reason_phrase)
        return True

    async def get_members(self):
        """ "async generator which yield valid user_id, member_type, email, mobile,"""
        data = {
            "exportDetails": {
                "Filename": "Medlemmer/Profiler",
                "Headline": None,
                "Lines": None,
            },
            "columns": "",
            "filter": {
                "tableSearch": "",
                "showMembersOnly": True,
                "showNonMembersOnly": False,
                "filterByFirstname": "",
                "filterBySurname": "",
                "columnFilter": None,
                "columnSearch": None,
                "filterByProfileId": 0,
            },
            "search": "",
            "order": None,
        }
        try:
            response = await self.client.post(
                "/Adminv2/SearchProfile/ExportCsv",
                json=data,
                timeout=60.0,  # crazy slow
            )
        except httpx.TimeoutException:
            raise KlubmodulException("failed to get member profiles due to timeout")
        if response.is_error:
            raise KlubmodulException(
                "failed to get member profiles: " + response.reason_phrase
            )
        for row in csv.DictReader(response.iter_lines(), delimiter=";", quotechar='"'):
            user_id = int(row["Id"])
            member_type = (
                "FULL" if "1" in row["Hold"] else "MORN" if "2" in row["Hold"] else None
            )
            name = row["Fornavn"].capitalize() + " " + row["Efternavn"].capitalize()
            email = row["Email"].lower()
            mobile = row["Mobil"]
            if member_type:
                yield user_id, name, member_type, email, mobile

    async def send_sms(
        self, user_id: int, message: str, delete_delay: int = 10
    ) -> None:
        data = {
            "rowData": [
                {"columnName": "broadcast_media", "value": "sms"},
                {"columnName": "send_email", "value": "savedraft"},
                {"columnName": "sms_text", "value": message},
                {"columnName": "subject", "value": ""},
                {
                    "columnName": "answer_email",
                    "value": f"{settings.klubmodul_admin_user_id}",
                },
                {"columnName": "mail_text", "value": "\r\n"},
                {"columnName": "test_email", "value": ""},
                {"columnName": "is_news_mail", "value": False},
                {"columnName": "is_all_team_member_profiles", "value": False},
                {"columnName": "is_all_team_nonmember_profiles", "value": False},
                {"columnName": "dd_target_teams", "values": []},
                {"columnName": "dd_target_team_names", "values": []},
                {"columnName": "dd_target_days", "values": []},
                {"columnName": "dd_target_season", "value": None},
                {"columnName": "dd_target_all_profiles", "values": [f"{user_id}"]},
                {"columnName": "dd_target_titles", "values": []},
                {"columnName": "titles_as_filter", "value": False},
                {"columnName": "dd_target_ages", "values": []},
                {"columnName": "ages_as_filter", "value": False},
                {"columnName": "dd_target_vintages", "values": []},
                {"columnName": "vintages_as_filter", "value": False},
                {"columnName": "dd_target_pools", "values": []},
                {"columnName": "dd_target_genders", "values": []},
                {"columnName": "genders_as_filter", "value": False},
                {"columnName": "dd_target_promotion_team_names", "values": []},
                {"columnName": "dd_target_profiles", "values": [f"{user_id}"]},
            ],
            "extraArgs": {
                "formValues": [
                    {"columnName": "broadcast_media", "value": "sms"},
                    {"columnName": "send_email", "value": "savedraft"},
                    {"columnName": "sms_text", "value": ""},
                    {"columnName": "subject", "value": ""},
                    {
                        "columnName": "answer_email",
                        "value": f"{settings.klubmodul_admin_user_id}",
                    },
                    {"columnName": "mail_text", "value": "\r\n"},
                    {"columnName": "test_email", "value": ""},
                    {"columnName": "is_news_mail", "value": False},
                    {"columnName": "is_all_team_member_profiles", "value": False},
                    {"columnName": "is_all_team_nonmember_profiles", "value": False},
                    {"columnName": "dd_target_teams", "values": []},
                    {"columnName": "dd_target_team_names", "values": []},
                    {"columnName": "dd_target_days", "values": []},
                    {"columnName": "dd_target_season", "value": None},
                    {"columnName": "dd_target_all_profiles", "values": [f"{user_id}"]},
                    {"columnName": "dd_target_titles", "values": []},
                    {"columnName": "titles_as_filter", "value": False},
                    {"columnName": "dd_target_ages", "values": []},
                    {"columnName": "ages_as_filter", "value": False},
                    {"columnName": "dd_target_vintages", "values": []},
                    {"columnName": "vintages_as_filter", "value": False},
                    {"columnName": "dd_target_pools", "values": []},
                    {"columnName": "dd_target_genders", "values": []},
                    {"columnName": "genders_as_filter", "value": False},
                    {"columnName": "dd_target_promotion_team_names", "values": []},
                    {"columnName": "dd_target_profiles", "values": []},
                ]
            },
        }
        try:
            response = await self.client.post(
                "/Adminv2/NewsMail/__Create", json=data, timeout=10.0
            )
        except httpx.TimeoutException:
            raise KlubmodulException("send sms timeout")
        if response.is_error:
            raise KlubmodulException("send sms server error: " + response.reason_phrase)
        save_id = response.json()["savedId"]

        # cleanup after ourself again by removing the sms in klubmodul mail/sms overview
        if delete_delay:
            await asyncio.sleep(delete_delay)
        try:
            response = await self.client.request(
                method="DELETE",
                url="/Adminv2/Newsmail/__Delete",
                json={"rowId": f"sms-{save_id}"},
                timeout=10.0,
            )
        except httpx.TimeoutException:
            raise KlubmodulException("send sms remove trail timeout")
        if response.is_error:
            raise KlubmodulException("send sms remove trail: " + response.reason_phrase)

    async def send_email(
        self, user_id: int, subject: str, message: str, delete_delay: int = 10
    ) -> None:
        data = {
            "rowData": [
                {"columnName": "broadcast_media", "value": "email"},
                {"columnName": "send_email", "value": "sendemail"},
                {"columnName": "sms_text", "value": ""},
                {"columnName": "subject", "value": subject},
                {
                    "columnName": "answer_email",
                    "value": f"{settings.klubmodul_admin_user_id}",
                },
                {"columnName": "mail_text", "value": message},
                {"columnName": "test_email", "value": ""},
                {"columnName": "is_news_mail", "value": False},
                {"columnName": "is_all_team_member_profiles", "value": False},
                {"columnName": "is_all_team_nonmember_profiles", "value": False},
                {"columnName": "dd_target_teams", "values": []},
                {"columnName": "dd_target_team_names", "values": []},
                {"columnName": "dd_target_days", "values": []},
                {"columnName": "dd_target_waitinglist", "values": []},
                {"columnName": "dd_target_season", "value": None},
                {"columnName": "dd_target_all_profiles", "values": [f"{user_id}"]},
                {"columnName": "dd_target_titles", "values": []},
                {"columnName": "titles_as_filter", "value": False},
                {"columnName": "dd_target_ages", "values": []},
                {"columnName": "ages_as_filter", "value": False},
                {"columnName": "dd_target_vintages", "values": []},
                {"columnName": "vintages_as_filter", "value": False},
                {"columnName": "dd_target_pools", "values": []},
                {"columnName": "dd_target_genders", "values": []},
                {"columnName": "genders_as_filter", "value": False},
                {"columnName": "dd_target_promotion_team_names", "values": []},
                {"columnName": "dd_target_profiles", "values": [f"{user_id}"]},
            ],
            "extraArgs": {
                "formValues": [
                    {"columnName": "broadcast_media", "value": "email"},
                    {"columnName": "send_email", "value": "savedraft"},
                    {"columnName": "sms_text", "value": ""},
                    {"columnName": "subject", "value": subject},
                    {
                        "columnName": "answer_email",
                        "value": f"{settings.klubmodul_admin_user_id}",
                    },
                    {"columnName": "mail_text", "value": message},
                    {"columnName": "test_email", "value": ""},
                    {"columnName": "is_news_mail", "value": False},
                    {"columnName": "is_all_team_member_profiles", "value": False},
                    {
                        "columnName": "is_all_team_nonmember_profiles",
                        "value": False,
                    },
                    {"columnName": "dd_target_teams", "values": []},
                    {"columnName": "dd_target_team_names", "values": []},
                    {"columnName": "dd_target_days", "values": []},
                    {"columnName": "dd_target_waitinglist", "values": []},
                    {"columnName": "dd_target_season", "value": None},
                    {
                        "columnName": "dd_target_all_profiles",
                        "values": [f"{user_id}"],
                    },
                    {"columnName": "dd_target_titles", "values": []},
                    {"columnName": "titles_as_filter", "value": False},
                    {"columnName": "dd_target_ages", "values": []},
                    {"columnName": "ages_as_filter", "value": False},
                    {"columnName": "dd_target_vintages", "values": []},
                    {"columnName": "vintages_as_filter", "value": False},
                    {"columnName": "dd_target_pools", "values": []},
                    {"columnName": "dd_target_genders", "values": []},
                    {"columnName": "genders_as_filter", "value": False},
                    {"columnName": "dd_target_promotion_team_names", "values": []},
                    {"columnName": "dd_target_profiles", "values": []},
                ]
            },
        }
        try:
            response = await self.client.post(
                "/Adminv2/NewsMail/__Create", json=data, timeout=10.0
            )
        except httpx.TimeoutException:
            raise KlubmodulException("send email timeout")
        if response.is_error:
            raise KlubmodulException(
                "send email server error: " + response.reason_phrase
            )
        save_id = response.json()["savedId"]

        # cleanup after ourself again by removing the sms in klubmodul mail/sms overview
        if delete_delay:
            await asyncio.sleep(delete_delay)
        try:
            response = await self.client.request(
                method="DELETE",
                url="/Adminv2/Newsmail/__Delete",
                json={"rowId": f"newsmail-{save_id}"},
                timeout=10.0,
            )
        except httpx.TimeoutException:
            raise KlubmodulException("send email remove trail timeout")
        if response.is_error:
            raise KlubmodulException(
                "send email remove trail: " + response.reason_phrase
            )

    async def __aenter__(self: U) -> U:
        await self._km_login()
        return self

    async def aclose(self) -> None:
        await self.client.aclose()

    async def __aexit__(
        self,
        exc_type: typing.Optional[typing.Type[BaseException]] = None,
        exc_value: typing.Optional[BaseException] = None,
        traceback: typing.Optional[TracebackType] = None,
    ) -> None:
        await self.client.aclose()


class KlubmodulException(Exception):
    pass


async def refresh():
    async with refresh_lock:
        batch_id = datetime.now(tz=settings.tz).isoformat(timespec="seconds")
        async with KMClient() as client, aiosqlite.connect(settings.db_file) as conn:
            async for user_id, name, member_type, email, mobile in client.get_members():
                await queries.upsert_user(
                    conn,
                    user_id=user_id,
                    name=name,
                    member_type=member_type,
                    email=simple_hash(email),
                    mobile=simple_hash(mobile),
                    batch_id=batch_id,
                    totp_secret=pyotp.random_base32(),
                    active=True,
                )
            # mark old data as inactive
            await queries.inactivate_old_batch(conn, batch_id=batch_id)
            await conn.commit()


async def klubmodul_runner(one_time_run: bool = False):
    # a bit of initial sleeping for two hours
    await asyncio.sleep(2 * 60 * 60)
    while True:
        try:
            log.info("klubmodul refreshing data")
            await refresh()
            log.info("klubmodul refresh done")
            # sleep until tomorrow
            await asyncio.sleep(24 * 60 * 60)
        except (KlubmodulException, Exception) as ex:
            log.error(f"failed to fetch klubmodul data retry in an hour {ex}")
            await asyncio.sleep(60 * 60)
        if one_time_run:
            break


# async def tester():
#     async with KMClient() as client:
#         await client.send_sms(user_id=3587, message="123456")
#     #     results = [item async for item in client.get_members()]
#     # pprint(results)
#     # print(len(results))
#     # print(len([i for i in results if i[1] == "MORN"]))
#     # print(len([i for i in results if i[1] == "FULL"]))


# if __name__ == "__main__":
#     asyncio.run(tester())
