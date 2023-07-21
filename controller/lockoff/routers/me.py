from typing import Annotated

from fastapi import APIRouter, Security

from ..access_token import generate_dl_token
from ..db import queries
from ..depends import DBcon, get_current_mobile

router = APIRouter(tags=["card"])


@router.get("/me")
async def me(
    mobile: Annotated[str, Security(get_current_mobile, scopes=["basic"])],
    conn: DBcon,
):
    users = await queries.get_active_users_by_mobile(conn, mobile=mobile)
    return [
        {
            "user_id": user["user_id"],
            "name": user["name"],
            "token": generate_dl_token(user["user_id"]),
        }
        for user in users
    ]
