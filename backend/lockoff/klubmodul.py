from datetime import datetime

import httpx

from . import db
from .utils import Member, TokenEnum

TEAMS = {
    111: TokenEnum.full,
    112: TokenEnum.morning,
}


class Klubmodul:
    def __init__(
        self, username: str, password: str, country_id: int = 1, club_id: int = 2002
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
                raise Exception("failed to login: " + response.reason_phrase)
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
                    raise Exception(
                        "failed to receive members by team: " + response.reason_phrase
                    )
                members += [
                    Member(name=d["ProfileName"], member_type=team_type, token="")
                    for d in response.json().get("d")
                ]
            return members

    async def refresh(self):
        members = await self.get_members()
        async with db.database.transaction():
            batch = datetime.utcnow()
            insert = db.tokens.insert().values(
                [
                    {
                        "batch": batch,
                        "name": member.name,
                        "token": member.token,
                        "token_type": member.token_type,
                        "last_access": batch,
                    }
                    for member in members
                ]
            )
            upsert = insert.on_conflict_do_update(
                index_elements=[db.tokens.c.token.name],
                set_=dict(
                    batch=batch,
                    name=insert.excluded.name,
                    token=insert.excluded.token,
                ),
            )
            # bulk upsert all users from klubmodul
            await db.database.execute(upsert)
            # remove full/morning users not in this batch
            await db.database.execute(
                db.tokens.delete().where(
                    db.tokens.c.token_type.in_([TokenEnum.full, TokenEnum.morning]),
                    db.tokens.c.batch.name < batch,
                )
            )
