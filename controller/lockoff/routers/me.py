from typing import Annotated

from fastapi import APIRouter, Security

from .. import schemas
from ..access_token import generate_dl_token
from ..config import settings
from ..depends import DBcon, get_current_user_ids
from ..misc import queries

router = APIRouter(tags=["me"])


@router.get("/me")
async def me(
    user_ids: Annotated[str, Security(get_current_user_ids, scopes=["basic"])],
    conn: DBcon,
) -> schemas.MeReply:
    users = await queries.get_active_users_by_user_ids(conn, user_ids=user_ids)
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
