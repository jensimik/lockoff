from typing import Annotated

from fastapi import APIRouter, Security

from lockoff import depends

from ..depends import DBcon
from ..misc import queries

router = APIRouter(prefix="/admin", tags=["admin"])


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
async def members_without_danish_mobile(
    mobile: Annotated[str, Security(depends.get_current_mobile, scopes=["admin"])],
):
    pass


@router.post("/send-membercard-by-email")
async def send_membercard_by_email(
    mobile: Annotated[str, Security(depends.get_current_mobile, scopes=["admin"])],
):
    pass
    # send membercard to a member manually (to those with no danish mobile number in klubmodul?)


@router.get("/system-status")
async def system_status(
    mobile: Annotated[str, Security(depends.get_current_mobile, scopes=["admin"])],
):
    pass
    # return all alive?
    # last x access_log
    # estimated number of day-tickets left in reception?
