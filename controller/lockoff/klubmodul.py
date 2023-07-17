import asyncio
import csv
import logging
import typing
from datetime import datetime
from types import TracebackType

import httpx
from tinydb import operations, where
from tinydb.table import Document

from .config import settings
from .db import DB_member

log = logging.getLogger(__name__)

U = typing.TypeVar("U", bound="KMClient")


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
                data={
                    "__EVENTTARGET": "ctl00$ctl00",
                    "__EVENTARGUMENT": "",
                    "__VIEWSTATE": "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",
                    "__VIEWSTATEGENERATOR": "B92176B9",
                    "__EVENTVALIDATION": "939g888AoPEo044jSzoFDr26e5Q6pLKoamA9Ff9xzKSsP6uu4VPRc/F3R0R9fy6EEFU+KEmhOXm4q4e8e2NXpmgtK7zypoDvF884iGgAVxYf0IxwV3QasacdmMZ+9yhL+8ZCVvU+ptF1RhamLt7ZygQv6Ju9rGn5ZKWFaRb/VTt7ZPZj4bis9S63O5kq2byUCJqKulQQO1v8hgOhjFubUhesfhTdEzkDXQ7KubYpdZMTFFRbYwtIZLrXubkkGXyWdeLAgvEXHN8zSkNcTJ1FYAh9q1RdpCGBK1toxZeGNlA=",
                    "ctl00$txtUsername": settings.klubmodul_username,
                    "ctl00$txtPassword": settings.klubmodul_password,
                    "ctl00$chkKeepmeSignIN": "on",
                },
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
            email = row["Email"]
            mobile = row["Mobil"]
            if member_type:
                yield user_id, member_type, email, mobile

    async def send_sms(self, user_id: int, message: str) -> None:
        data = {
            "rowData": [
                {"columnName": "broadcast_media", "value": "sms"},
                {"columnName": "send_email", "value": "savedraft"},
                {"columnName": "sms_text", "value": message},
                {"columnName": "subject", "value": ""},
                {"columnName": "answer_email", "value": "3535"},
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
                    {"columnName": "answer_email", "value": "3535"},
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
    batch_id = datetime.utcnow().isoformat(timespec="seconds")
    async with DB_member as db, KMClient() as client:
        async for user_id, member_type, email, mobile in client.get_members():
            db.upsert(
                Document(
                    {
                        "level": member_type,
                        "mobile": mobile,
                        "email": email,
                        "batch_id": batch_id,
                        "active": True,
                    },
                    doc_id=user_id,
                )
            )
        # mark old data as inactive
        db.update(operations.set("active", False), where("batch_id") < batch_id)


async def klubmodul_runner():
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


async def tester():
    async with KMClient() as client:
        await client.send_sms(user_id=3587, message="123456")
    #     results = [item async for item in client.get_members()]
    # pprint(results)
    # print(len(results))
    # print(len([i for i in results if i[1] == "MORN"]))
    # print(len([i for i in results if i[1] == "FULL"]))


if __name__ == "__main__":
    asyncio.run(tester())
