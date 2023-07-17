import hashlib
import logging
from datetime import datetime, timedelta

import pyotp
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi_limiter.depends import RateLimiter
from pydantic import BaseModel
from tinydb import where, operations

from ..config import settings
from ..db import DB_member
from ..klubmodul import KMClient

router = APIRouter(tags=["auth"])
log = logging.getLogger(__name__)


class RAC(BaseModel):
    mobile: str


@router.post(
    "/request-auth-code", dependencies=[Depends(RateLimiter(times=5, seconds=300))]
)
async def request_auth_code(rac: RAC):
    async with DB_member as db:
        user_ids = [
            user.doc_id
            for user in db.search(
                (where("mobile") == rac.mobile) & (where("active") == True)
            )
        ]
    log.info(f"user_ids: {user_ids}")
    if user_ids:
        hotp_secret = pyotp.random_base32()
        hotp = pyotp.HOTP(hotp_secret)
        async with DB_member as db:
            db.update(operations.set("hotp_secret", hotp_secret), doc_ids=user_ids)
        async with KMClient() as km:
            # await km.send_sms(user_id=user_ids[0], message="123456")
            log.info(f"km.send_sms(user_id={user_ids[0]}, message={hotp.now()})")
    return {"status": "sms sent"}


@router.post("/login", dependencies=[Depends(RateLimiter(times=5, seconds=300))])
async def login():
    pass


@router.post(
    "/get-download-urls", dependencies=[Depends(RateLimiter(times=5, seconds=300))]
)
async def get_download_urls():
    # valid
    user_id = 1
    member_type = "full"
    expire = datetime(2024, 1, 1, 12, 0, 0).isoformat(timespec="seconds")
    url_expire = (datetime.datetime.utcnow() + timedelta(hours=24)).isoformat(
        timespec="seconds"
    )
    hashlib.sha256("{user_id}{url_expire}{secret}".encode("utf-8")).hexdigest()
    return {"pkpass": "", "pdf": ""}
