from typing import Annotated

import aiosqlite
from fastapi import APIRouter, Security

from .. import schemas
from ..access_token import generate_dl_token
from ..config import settings
from ..depends import DBcon, get_current_users
from ..misc import queries

router = APIRouter(tags=["me"])


@router.get("/me")
async def me(
    users: Annotated[
        list[aiosqlite.Row], Security(get_current_users, scopes=["basic"])
    ],
) -> schemas.MeReply:
    return schemas.MeReply(
        users=[
            {
                "user_id": user["user_id"],
                "name": user["name"],
                "token": generate_dl_token(user["user_id"]),
            }
            for user in users
        ],
    )
