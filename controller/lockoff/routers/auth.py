import logging
from datetime import datetime, timedelta

import pyotp
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi_limiter.depends import RateLimiter
from jose import jwt

from .. import schemas
from ..config import settings
from ..depends import DBcon
from ..klubmodul import KMClient
from ..misc import queries, simple_hash
from ..db import Users

router = APIRouter(tags=["auth"])
log = logging.getLogger(__name__)


async def send_mobile(user_id: int, message: str):
    async with KMClient() as km:
        await km.send_sms(user_id=user_id, message=message)
    log.info(f"sms sent to {user_id}")


async def send_email(user_id: int, message: str):
    async with KMClient() as km:
        await km.send_email(user_id=user_id, subject="AUTHMSG", message=message)
    log.info(f"email sent to {user_id}")


send_funcs = {
    "email": send_email,
    "mobile": send_mobile,
}


@router.post(
    "/request-totp", dependencies=[Depends(RateLimiter(times=10, seconds=300))]
)
async def request_totp(
    rt: schemas.RequestTOTP, conn: DBcon, background_tasks: BackgroundTasks
) -> schemas.StatusReply:
    if rt.username_type == "email":
        users = await Users.select(Users.user_id, Users.totp_secret).where(
            Users.email == simple_hash(rt.username)
        )
    elif rt.username_type == "mobile":
        users = await Users.select(Users.user_id, Users.totp_secret).where(
            Users.mobile == simple_hash(rt.username)
        )
    user_ids = [u["user_id"] for u in users]
    if user_ids:
        totp = pyotp.TOTP(users[0]["totp_secret"])
        log.info(
            f"send_{rt.username_type}(user_id={user_ids[0]}, message={totp.now()})"
        )
        code = totp.now()
        background_tasks.add_task(
            send_funcs[rt.username_type],
            user_id=user_ids[0],
            message=f"code is {code}\n\n@nkk.dk #{code}",
        )
    else:
        log.error("no users found!?")
    return schemas.StatusReply(status=f"{rt.username_type} message sent")


@router.post("/login", dependencies=[Depends(RateLimiter(times=10, seconds=300))])
async def login(
    login_data: schemas.RequestLogin,
    conn: DBcon,
) -> schemas.JWTToken:
    username_hash = simple_hash(login_data.username)
    if login_data.username_type == "email":
        users = await Users.select(Users.user_id, Users.totp_secret).where(
            Users.email == username_hash
        )
    elif login_data.username_type == "mobile":
        users = await Users.select(Users.user_id, Users.totp_secret).where(
            Users.mobile == username_hash
        )
    if not users:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="no such user, code is expired or not valid",
        )
    totp_secrets = [u["totp_secret"] for u in users]
    user_ids = [u["user_id"] for u in users]
    totp = pyotp.TOTP(totp_secrets[0])
    if not totp.verify(otp=login_data.totp, valid_window=2):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="no such user, code is expired or not valid",
        )
    # give basic scope to all
    scopes = ["basic"]
    # or basic+admin if in the special admin_user_ids list
    if set(settings.admin_user_ids) & set(user_ids):
        scopes = ["basic", "admin"]
    encoded_jwt = jwt.encode(
        {
            "sub": username_hash,
            "sub_type": login_data.username_type,
            "scopes": scopes,
            "exp": datetime.utcnow() + timedelta(hours=2),
        },
        settings.jwt_secret,
        algorithm="HS256",
    )
    return schemas.JWTToken(access_token=encoded_jwt, token_type="bearer")
