import asyncio
import logging
from datetime import datetime, timedelta
from typing import Annotated

import pyotp
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_limiter.depends import RateLimiter
from jose import jwt
from tinydb import operations, where

from .. import schemas
from ..config import settings
from ..db import DB_member
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
    rac: schemas.RequestTOTP, background_tasks: BackgroundTasks
) -> schemas.StatusReply:
    async with DB_member as db:
        user_ids = [
            user.doc_id
            for user in db.search(
                (where("mobile") == rac.mobile) & (where("active") == True)
            )
        ]
    if user_ids:
        totp_secret = pyotp.random_base32()
        totp = pyotp.TOTP(totp_secret)
        async with DB_member as db:
            db.update(operations.set("totp_secret", totp_secret), doc_ids=user_ids)
        log.info(f"km.send_sms(user_id={user_ids[0]}, message={totp.now()})")
        background_tasks.add_task(
            send_sms, user_id=user_ids[0], message=f"{totp.now()}"
        )
    else:
        await asyncio.sleep(4)
    return schemas.StatusReply(status="sms sent")


@router.post("/login", dependencies=[Depends(RateLimiter(times=105, seconds=300))])
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()]
) -> schemas.JWTToken:
    async with DB_member as db:
        users = db.search(
            (where("mobile") == form_data.username) & (where("active") == True)
        )
    if not users:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="mobile not found or code expired or not valid",
        )
    totp = pyotp.TOTP(users[0]["totp_secret"])
    if not totp.verify(otp=form_data.password, valid_window=2):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="code is expired or not valid"
        )
    encoded_jwt = jwt.encode(
        {
            "sub": form_data.username,
            "exp": datetime.utcnow() + timedelta(hours=2),
        },
        settings.jwt_secret,
        algorithm="HS256",
    )
    return schemas.JWTToken(access_token=encoded_jwt, token_type="bearer")
