import logging

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request, status
from fastapi_limiter.depends import RateLimiter

router = APIRouter(tags=["auth"])
log = logging.getLogger(__name__)


# allow 2 requests per 5 request per 5 minutes per ip
@router.post("/login1", dependencies=[Depends(RateLimiter(times=5, seconds=300))])
async def login(request: Request):
    log.info(f"client_host: {request.client.host}")
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        ip = forwarded.split(",")[0]
        log.info(f"x-forwarded-for: {ip}")

    return {"status": "sms sent"}
