from datetime import datetime
from typing import Annotated

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Security

from .. import schemas
from ..access_token import generate_dl_member_token, TokenType
from ..db import UserModel
from ..depends import get_current_users

router = APIRouter(tags=["me"])


@router.get("/me")
async def me(
    users: Annotated[list[UserModel], Security(get_current_users, scopes=["basic"])],
) -> schemas.MeReply:
    expires_display = datetime.utcnow() + relativedelta(
        day=1, month=1, years=1, hour=0, minute=0, second=0, microsecond=0
    )
    return schemas.MeReply(
        users=[
            {
                "user_id": user.id,
                "name": user.name,
                "token": generate_dl_member_token(user.id),
                "member_type": TokenType(user.token_type).name.lower(),
                "expires": "{0:%m/%y}".format(expires_display),
            }
            for user in users
        ],
    )


@router.get("/testing123")
async def testing123():
    from ..card.apple_pass import AppleNotifier
    from ..db import APPass, APDevice

    for d in await APDevice.select():
        print(d)
        async with AppleNotifier() as an:
            await an.notify_update(
                device_library_identifier=d["id"], push_token=d["push_token"]
            )
    return {"status": "ok"}
