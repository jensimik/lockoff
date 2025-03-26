import logging
from datetime import datetime

from fastapi import APIRouter, Security, HTTPException, status, Depends
from dateutil.relativedelta import relativedelta

from ..config import settings
from ..db import DB, Dayticket

from ..access_token import TokenMedia, TokenType, generate_access_token
from fastapi.security import APIKeyHeader

router = APIRouter(tags=["dayticket"])
log = logging.getLogger(__name__)

api_key_header = APIKeyHeader(name="ext_dayticket_token", auto_error=False)


async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == settings.ext_dayticket_token:
        return api_key_header
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"reason": "Could not validate API KEY"},
        )


@router.get("/single-dayticket", dependencies=[Depends(get_api_key)])
async def get_dayticket():
    batch_id = datetime.now(tz=settings.tz).isoformat(timespec="seconds")
    async with DB.transaction():
        ticket_id = await Dayticket.insert(
            Dayticket(id=None, batch_id=batch_id)
        ).returning(Dayticket.id)[0]["id"]
    access_token = generate_access_token(
        user_id=ticket_id,
        token_type=TokenType.DAY_TICKET,
        token_media=TokenMedia.PRINT,
        expire_delta=relativedelta(days=2),
    )
    return {
        "dayticket_id": ticket_id,
        "qr_code": access_token,
    }
