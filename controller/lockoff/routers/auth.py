import asyncio
import hashlib
import logging
from datetime import datetime, timedelta
from typing import Annotated

import pyotp
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi_limiter.depends import RateLimiter
from jose import JWTError, jwt
from tinydb import operations, where

from .. import schemas
from ..config import settings
from ..db import DB_member
from ..klubmodul import KMClient

router = APIRouter(tags=["auth"])
log = logging.getLogger(__name__)


@router.post("/request-totp", dependencies=[Depends(RateLimiter(times=5, seconds=300))])
async def request_totp(rac: schemas.RequestTOTP) -> schemas.StatusReply:
    async with DB_member as db:
        user_ids = [
            user.doc_id
            for user in db.search(
                (where("mobile") == rac.mobile) & (where("active") == True)
            )
        ]
    log.info(f"user_ids: {user_ids}")
    if user_ids:
        totp_secret = pyotp.random_base32()
        totp = pyotp.TOTP(totp_secret)
        async with DB_member as db:
            db.update(operations.set("totp_secret", totp_secret), doc_ids=user_ids)
        # async with KMClient() as km:
        #     await km.send_sms(user_id=user_ids[0], message=f"{totp.now()}")
        log.info(f"km.send_sms(user_id={user_ids[0]}, message={totp.now()})")
    else:
        await asyncio.sleep(4)
    return schemas.StatusReply(status="sms sent")


@router.post("/login", dependencies=[Depends(RateLimiter(times=5, seconds=300))])
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
    return schemas.JWTToken(token=encoded_jwt, token_type="bearer")
