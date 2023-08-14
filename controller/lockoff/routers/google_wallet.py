import logging

from fastapi import APIRouter, Request

from ..config import settings

router = APIRouter(prefix="/v1", tags=["google_wallet"])

log = logging.getLogger(__name__)


@router.post("/callback")
async def callback(request: Request):
    print(request.headers)
    print(await request.json())
