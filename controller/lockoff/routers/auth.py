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
from ..depends import DBcon
from ..klubmodul import KMClient
from ..misc import queries

router = APIRouter(tags=["auth"])
log = logging.getLogger(__name__)


async def send_sms(user_id: int, message: str):
    async with KMClient() as km:
        await km.send_sms(user_id=user_id, message=message)


async def send_email(user_id: int, subject: str, message: str):
    async with KMClient() as km:
        await km.send_email(user_id=user_id, subject=subject, message=message)


@router.post(
    "/request-mobile-totp", dependencies=[Depends(RateLimiter(times=105, seconds=300))]
)
async def request_mobile_totp(
    rt: schemas.RequestMobileTOTP, conn: DBcon, background_tasks: BackgroundTasks
) -> schemas.StatusReply:
    users = await queries.get_active_users_by_mobile(conn, mobile=rt.mobile)
    user_ids = [u["user_id"] for u in users]
    if user_ids:
        totp_secret = pyotp.random_base32()
        totp = pyotp.TOTP(totp_secret)
        await queries.update_user_by_mobile_set_totp_secret(
            conn, mobile=rt.mobile, totp_secret=totp_secret
        )
        await conn.commit()
        log.info(f"send_sms(user_id={user_ids[0]}, message={totp.now()})")
        background_tasks.add_task(
            send_sms, user_id=user_ids[0], message=f"{totp.now()}"
        )
    return schemas.StatusReply(status="sms sent")


@router.post(
    "/request-email-totp", dependencies=[Depends(RateLimiter(times=105, seconds=300))]
)
async def request_mobile_totp(
    rt: schemas.RequestEmailTOTP, conn: DBcon, background_tasks: BackgroundTasks
) -> schemas.StatusReply:
    users = await queries.get_active_users_by_email(conn, mobile=rt.email)
    user_ids = [u["user_id"] for u in users]
    if user_ids:
        totp_secret = pyotp.random_base32()
        totp = pyotp.TOTP(totp_secret)
        await queries.update_user_by_email_set_totp_secret(
            conn, mobile=rt.email, totp_secret=totp_secret
        )
        await conn.commit()
        log.info(
            f"send_email(user_id={user_ids[0]}, subject=AUTHMSG, message={totp.now()})"
        )
        background_tasks.add_task(
            send_email, user_id=user_ids[0], subject="AUTHMSG", message=f"{totp.now()}"
        )
    return schemas.StatusReply(status="sms sent")


@router.post("/login", dependencies=[Depends(RateLimiter(times=105, seconds=300))])
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], conn: DBcon
) -> schemas.JWTToken:
    users = await queries.get_active_users_by_mobile_or_email(
        conn, username=form_data.username
    )
    totp_secrets = [u["totp_secret"] for u in users]
    user_ids = [u["user_id"] for u in users]
    if not totp_secrets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="mobile not found or code expired or not valid",
        )
    totp = pyotp.TOTP(totp_secrets[0])
    if not totp.verify(otp=form_data.password, valid_window=2):
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
            "sub": " ".join(user_ids),  # specific user_ids
            "scopes": scopes,
            "exp": datetime.utcnow() + timedelta(hours=2),
        },
        settings.jwt_secret,
        algorithm="HS256",
    )
    return schemas.JWTToken(access_token=encoded_jwt, token_type="bearer")
