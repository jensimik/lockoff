import logging
from datetime import datetime, timedelta
import hashlib

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi_limiter.depends import RateLimiter

from ..klubmodul import KMClient
from ..config import settings
from ..db import DB_member
from tinydb import where

router = APIRouter(tags=["auth"])
log = logging.getLogger(__name__)


@router.post(
    "/request-auth-code", dependencies=[Depends(RateLimiter(times=5, seconds=300))]
)
async def request_auth_code(mobile: int):
    # with DB_member as db:
    #     for db.search(where("mobile") == mobile)
    # # TODO: lookup mobile if it exists in database?
    # with KMClient() as km:
    #     await km.send_sms(user_id=1, message=)
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
