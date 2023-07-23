from typing import Annotated

from fastapi import APIRouter, Security

from .. import schemas
from ..access_token import generate_dl_token
from ..config import settings
from ..depends import DBcon, get_current_user_id
from ..misc import queries

router = APIRouter(tags=["me"])


@router.get("/me")
async def me(
    user_id: Annotated[str, Security(get_current_user_id, scopes=["basic"])],
    conn: DBcon,
) -> schemas.MeReply:
    user = await queries.get_active_user_by_id(conn, user_id=user_id)
    # get all users with same mobile or email as this user
    users = await queries.get_active_users_by_mobile_or_email(
        conn, mobile=user["mobile"], email=user["email"]
    )
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
