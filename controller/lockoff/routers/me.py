from typing import Annotated

from fastapi import APIRouter, Security

from .. import schemas
from ..access_token import generate_dl_token
from ..db import queries
from ..depends import DBcon, get_current_mobile
from ..config import settings

router = APIRouter(tags=["me"])


@router.get("/me")
async def me(
    mobile: Annotated[str, Security(get_current_mobile, scopes=["basic"])],
    conn: DBcon,
) -> schemas.MeReply:
    users = await queries.get_active_users_by_mobile(conn, mobile=mobile)
    user_ids = [u["user_id"] for u in users]
    is_admin = bool(set(settings.admin_user_ids) & set(user_ids))
    return schemas.MeReply(
        is_admin=is_admin,
        users=[
            {
                "user_id": user["user_id"],
                "name": user["name"],
                "token": generate_dl_token(user["user_id"]),
            }
            for user in users
        ],
    )
