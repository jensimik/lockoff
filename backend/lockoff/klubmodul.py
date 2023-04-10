import asyncio
import logging

import httpx

from . import db
from .config import settings
from .utils import Member, TokenEnum

TEAMS = {
    111: TokenEnum.full,
    112: TokenEnum.morning,
}
log = logging.getLogger(__name__)


class KlubmodulException(Exception):
    pass


class Klubmodul:
    def __init__(
        self,
        username: str,
        password: str,
        country_id: int = settings.klubmodul_country_id,
        club_id: int = settings.klubmodul_club_id,
    ):
        self.username = username
        self.password = password
        self.country_id = country_id
        self.club_id = club_id

    async def get_members(self) -> list[Member]:
        async with httpx.AsyncClient(
            base_url="https://klubmodul-app.dk/admin/KlubModulAPI.asmx"
        ) as client:
            # login and get profile token and session cookie set
            response = await client.post(
                "/Login",
                json={
                    "username": self.username,
                    "password": self.password,
                    "clubid": self.club_id,
                },
            )
            if response.is_error:
                raise KlubmodulException("failed to login: " + response.reason_phrase)
            profile_creds = response.json().get("d")

            # get list of users in both teams (morning/full)
            members = []
            for team_id, team_type in TEAMS.items():
                post_data = {
                    "profileToken": profile_creds.get("ProfileToken", ""),
                    "teamID": team_id,
                }
                response = await client.post("/GetMembersByTeamID", json=post_data)
                if response.is_error:
                    raise KlubmodulException(
                        "failed to receive members by team: " + response.reason_phrase
                    )
                members += [
                    Member(
                        name=d["ProfileName"], member_type=team_type, token=""
                    )  # TODO: find field with birthday and last digits
                    for d in response.json().get("d")
                ]
            return members

    async def refresh(self):
        members = await self.get_members()
        await db.bulk_upsert_members(members)

    async def runner(self):
        while True:
            try:
                log.info("klubmodul refreshing data")
                self.refresh()
                log.info("klubmodul refresh done")
                asyncio.sleep(12 * 60 * 60)
            except KlubmodulException:
                log.error("failed to fetch klubmodul data retry in 5 minutes")
                asyncio.sleep(5 * 60)
