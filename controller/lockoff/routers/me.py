import logging
from datetime import datetime
from typing import Annotated

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Security

from .. import schemas
from ..access_token import TokenType, generate_dl_member_token
from ..db import UserModel
from ..depends import get_current_users

router = APIRouter(tags=["me"])
log = logging.getLogger(__name__)


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
    from ..db import APDevice, APPass, APReg

    async with AppleNotifier() as an:
        for p in await APPass.select(
            APPass.id,
            APPass.id.join_on(APReg.serial_number)
            .device_library_identifier.join_on(APDevice.id)
            .push_token.as_alias("push_token"),
        ):
            log.info(p)
            await an.notify_update(push_token=p["push_token"])
    return {"status": "ok"}
