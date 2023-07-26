from typing import Annotated

import aiosqlite
from fastapi import APIRouter, Security

from lockoff import depends

from ..depends import DBcon
from ..misc import queries

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/access_log")
async def access_log(
    users: Annotated[
        list[aiosqlite.Row], Security(depends.get_current_users, scopes=["admin"])
    ],
    conn: DBcon,
):
    return await queries.last_log_entries(conn, limit=30)


@router.post("/klubmodul-force-resync")
async def klubmodul_force_resync(
    users: Annotated[
        list[aiosqlite.Row], Security(depends.get_current_users, scopes=["admin"])
    ],
):
    pass


@router.get("/members-without-danish-mobile")
async def members_without_danish_mobile(
    users: Annotated[
        list[aiosqlite.Row], Security(depends.get_current_users, scopes=["admin"])
    ],
):
    pass


@router.post("/send-membercard-by-email")
async def send_membercard_by_email(
    users: Annotated[
        list[aiosqlite.Row], Security(depends.get_current_users, scopes=["admin"])
    ],
):
    pass
    # send membercard to a member manually (to those with no danish mobile number in klubmodul?)


@router.get("/system-status")
async def system_status(
    users: Annotated[
        list[aiosqlite.Row], Security(depends.get_current_users, scopes=["admin"])
    ],
):
    pass
    # last successful sync with klubmodul and number of users synced
    # return all alive?
    # last x access_log
    # estimated number of day-tickets left in reception?
