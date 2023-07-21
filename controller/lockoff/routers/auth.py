import logging
from datetime import datetime, timedelta
from typing import Annotated

import pyotp
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_limiter.depends import RateLimiter
from jose import jwt

from .. import schemas
from ..config import settings
from ..db import queries
from ..depends import DBcon
from ..klubmodul import KMClient

router = APIRouter(tags=["auth"])
log = logging.getLogger(__name__)


# @router.get("/test")
# async def test():
#     async with DB_member as db:
#         users = db.search(where("active") == True)

#     # fixup 45
#     for u in users:
#         if (
#             u["mobile"].startswith("45")
#             or u["mobile"].startswith("0045")
#             or u["mobile"].startswith("+45")
#             or u["mobile"].startswith("045")
#         ):
#             u["mobile"] = u["mobile"][-8:]
#     eight_digits = len([u for u in users if len(u["mobile"]) == 8])
#     other = len(users) - eight_digits

#     others = [u for u in users if len(u["mobile"]) != 8]

#     return {"eight_digits": eight_digits, "other": other, "others": others}


async def send_sms(user_id: int, message: str):
    async with KMClient() as km:
        await km.send_sms(user_id=user_id, message=message)


@router.post(
    "/request-totp", dependencies=[Depends(RateLimiter(times=105, seconds=300))]
)
async def request_totp(
    rt: schemas.RequestTOTP, conn: DBcon, background_tasks: BackgroundTasks
) -> schemas.StatusReply:
    users = await queries.get_active_users_by_mobile(conn, mobile=rt.mobile)
    user_ids = [u["user_id"] for u in users]
    if user_ids:
        totp_secret = pyotp.random_base32()
        totp = pyotp.TOTP(totp_secret)
        await queries.update_user_set_totp_secret(
            conn, mobile=rt.mobile, totp_secret=totp_secret
        )
        await conn.commit()
        log.info(f"send_sms(user_id={user_ids[0]}, message={totp.now()})")
        background_tasks.add_task(
            send_sms, user_id=user_ids[0], message=f"{totp.now()}"
        )
    return schemas.StatusReply(status="sms sent")


@router.post("/login", dependencies=[Depends(RateLimiter(times=105, seconds=300))])
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], conn: DBcon
) -> schemas.JWTToken:
    totp_secret = await queries.get_active_user_totp_secret_by_mobile(
        conn, mobile=form_data.username
    )
    if not totp_secret:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="mobile not found or code expired or not valid",
        )
    totp = pyotp.TOTP(totp_secret)
    if not totp.verify(otp=form_data.password, valid_window=2):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="code is expired or not valid",
        )
    # give basic scope to all
    scopes = "basic"
    # or basic+admin if in the special admin_user_ids list
    if int(form_data.username) in settings.admin_user_ids:
        scopes = "basic admin"
        print("gave admin scope")
    encoded_jwt = jwt.encode(
        {
            "sub": form_data.username,
            "scopes": scopes,
            "exp": datetime.utcnow() + timedelta(hours=2),
        },
        settings.jwt_secret,
        algorithm="HS256",
    )
    return schemas.JWTToken(access_token=encoded_jwt, token_type="bearer")
