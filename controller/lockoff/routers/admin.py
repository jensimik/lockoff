from datetime import datetime
from typing import Annotated

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, HTTPException, Response, Security, status

from lockoff import depends

from ..access_token import TokenType, generate_access_token
from ..apple_pass import ApplePass
from ..config import settings
from ..db import queries
from ..depends import DBcon

router = APIRouter(tags=["admin"])


@router.get("/access_log")
async def access_log(
    mobile: Annotated[str, Security(depends.get_current_mobile, scopes=["admin"])],
    conn: DBcon,
):
    return await queries.last_log_entries(conn, limit=30)


@router.post("/klubmodul-force-resync")
async def access_log(
    mobile: Annotated[str, Security(depends.get_current_mobile, scopes=["admin"])],
):
    pass


@router.get("/members-without-danish-mobile")
async def members_without_danish_mobile():
    pass


@router.post("/send-membercard-by-email")
async def send_membercard_by_email():
    pass
    # send membercard to a member manually (to those with no danish mobile number in klubmodul?)


@router.get("/system-status")
async def system_status():
    pass
    # return all alive?
    # last x access_log
    # estimated number of day-tickets left in reception?
