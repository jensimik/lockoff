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
from ..misc import queries

router = APIRouter(tags=["auth"])
log = logging.getLogger(__name__)


async def send_mobile(user_id: int, message: str):
    async with KMClient() as km:
        await km.send_sms(user_id=user_id, message=message)


async def send_email(user_id: int, message: str):
    async with KMClient() as km:
        await km.send_email(user_id=user_id, subject="AUTHMSG", message=message)


send_funcs = {
    "email": send_email,
    "mobile": send_mobile,
}


@router.post(
    "/request-totp", dependencies=[Depends(RateLimiter(times=105, seconds=300))]
)
async def request_totp(
    rt: schemas.RequestTOTP, conn: DBcon, background_tasks: BackgroundTasks
) -> schemas.StatusReply:
    # support either mobile or email as username_type
    users = await getattr(queries, f"get_active_users_by_{rt.username_type}")(
        conn, **{rt.username_type: rt.username}
    )
    user_ids = [u["user_id"] for u in users]
    if user_ids:
        totp_secret = pyotp.random_base32()
        totp = pyotp.TOTP(totp_secret)
        await getattr(queries, f"update_user_by_{rt.username_type}_set_totp_secret")(
            conn, totp_secret=totp_secret, **{rt.username_type: rt.username}
        )
        await conn.commit()

        log.info(
            f"send_{rt.username_type}(user_id={user_ids[0]}, message={totp.now()})"
        )
        code = totp.now()
        background_tasks.add_task(
            send_funcs[rt.username_type],
            user_id=user_ids[0],
            message=f"code is {code}\n\n@lockoff.nkk.dk #{code}",
        )
    return schemas.StatusReply(status=f"{rt.username_type} message sent")


@router.post("/login", dependencies=[Depends(RateLimiter(times=105, seconds=300))])
async def login(
    login_data: schemas.RequestLogin,
    conn: DBcon,
) -> schemas.JWTToken:
    users = await getattr(queries, f"get_active_users_by_{login_data.username_type}")(
        conn, **{login_data.username_type: login_data.username}
    )
    totp_secrets = [u["totp_secret"] for u in users]
    user_ids = [u["user_id"] for u in users]
    if not totp_secrets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="mobile not found or code expired or not valid",
        )
    totp = pyotp.TOTP(totp_secrets[0])
    if not totp.verify(otp=login_data.totp, valid_window=2):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="code is expired or not valid",
        )
    # give basic scope to all
    scopes = ["basic"]
    # or basic+admin if in the special admin_user_ids list
    if set(settings.admin_user_ids) & set(user_ids):
        scopes = ["basic", "admin"]
    encoded_jwt = jwt.encode(
        {
            "sub": login_data.username,
            "sub_type": login_data.username_type,
            "scopes": scopes,
            "exp": datetime.utcnow() + timedelta(hours=2),
        },
        settings.jwt_secret,
        algorithm="HS256",
    )
    return schemas.JWTToken(access_token=encoded_jwt, token_type="bearer")
