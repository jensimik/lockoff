import asyncio
import logging
from datetime import datetime

import httpx
from tinydb import where, set as tiny_set
from tinydb.table import Document

from .config import settings
from .db import DB_member
from .access_token import TokenType

TEAMS = {111: TokenType.NORMAL, 112: TokenType.MORNING}

log = logging.getLogger(__name__)


class KlubmodulException(Exception):
    pass


class Klubmodul:
    def __init__(
        self,
        username: str = settings.klubmodul_username,
        password: str = settings.klubmodul_password,
        country_id: int = settings.klubmodul_country_id,
        club_id: int = settings.klubmodul_club_id,
    ):
        self.username = username
        self.password = password
        self.country_id = country_id
        self.club_id = club_id

    async def get_members(self):
        """ "async generator which yield valid user_id, team_type"""
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
                for d in response.json().get("d"):
                    yield d["ProfileID_FK"], team_type

    async def refresh(self):
        batch_id = datetime.utcnow().isoformat(timespec="seconds")
        async with DB_member as db:
            async for user_id, team_type in self.get_members():
                db.upsert(
                    Document(
                        {
                            "level": team_type.value,
                            "batch_id": batch_id,
                            "email": "",  # TODO: get email somehow?
                            "active": True,
                        },
                        doc_id=user_id,
                    )
                )
            # mark old data as inactive
            db.update(tiny_set("active", False), where("batch_id") < batch_id)

            # loop through all and check if we should welcome email out
            for user in db.search(where("active") == True):
                if user.get("email_sent", 0) < settings.current_season:
                    # TODO: invite_mail_user(user_id=user.doc_id, email=user["email"])
                    db.update(
                        tiny_set("email_sent", settings.current_season),
                        doc_ids=[user.doc_id],
                    )

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
