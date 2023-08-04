from datetime import datetime
from typing import Annotated

import aiosqlite
from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Security

from .. import schemas
from ..access_token import generate_dl_member_token, TokenType
from ..depends import get_current_users

router = APIRouter(tags=["me"])


@router.get("/me")
async def me(
    users: Annotated[
        list[aiosqlite.Row], Security(get_current_users, scopes=["basic"])
    ],
) -> schemas.MeReply:
    expires_display = datetime.utcnow() + relativedelta(
        day=1, month=1, years=1, hour=0, minute=0, second=0, microsecond=0
    )
    return schemas.MeReply(
        users=[
            {
                "user_id": user["user_id"],
                "name": user["name"],
                "token": generate_dl_member_token(user["user_id"]),
                "member_type": user["member_type"].lower(),
                "expires": "{0:%m/%y}".format(expires_display),
            }
            for user in users
        ],
    )
