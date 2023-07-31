import io
from datetime import datetime
from typing import Annotated

import aiosqlite
from dateutil.relativedelta import relativedelta
from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    HTTPException,
    Response,
    Security,
    status,
)

from .. import depends, schemas
from ..access_token import (
    TokenType,
    generate_access_token,
    generate_dl_token,
    verify_dl_token,
)
from ..card import generate_png
from ..config import settings
from ..depends import DBcon
from ..klubmodul import refresh
from ..misc import queries

router = APIRouter(prefix="/admin", tags=["admin"])


@router.post("/generate-daytickets")
async def klubmodul_force_resync(
    _: Annotated[
        list[aiosqlite.Row], Security(depends.get_current_users, scopes=["admin"])
    ],
    conn: DBcon,
):
    batch_id = datetime.now(tz=settings.tz).isoformat(timespec="seconds")
    dayticket_ids = [
        await queries.insert_dayticket(conn, batch_id=batch_id) for _ in range(30)
    ]
    return [generate_dl_token(user_id=dayticket_id) for dayticket_id in dayticket_ids]


@router.get(
    "/{token}/qr-code.png",
    response_class=Response,
    responses={
        200: {"content": {"image/png": {}}},
    },
)
async def get_qr_code_png(
    ticket_id: Annotated[int, Depends(verify_dl_token)],
    conn: DBcon,
):
    ticket = await queries.get_dayticket_by_id(conn, ticket_id=ticket_id)
    if not ticket:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    access_token = generate_access_token(
        user_id=ticket_id,
        token_type=TokenType.DAY_TICKET_HACK,
        expire_delta=relativedelta(months=3),
    )
    img = generate_png(qr_code_data=access_token.decode())
    with io.BytesIO() as f:
        img.save(f, format="png")
        content = f.getvalue()
    return Response(content=content, media_type="image/png")


@router.get("/access_log")
async def access_log(
    _: Annotated[
        list[aiosqlite.Row], Security(depends.get_current_users, scopes=["admin"])
    ],
    conn: DBcon,
):
    return await queries.last_log_entries(conn, limit=30)


# from dateutil.rrule import rrulestr
# from dateutil.relativedelta import relativedelta
# from dateutil.tz import gettz
# from datetime import datetime

# tz = gettz("Europe/Copenhagen")

# today = datetime.now(tz=tz) + relativedelta(hour=0, minute=0, second=0, microsecond=0)
# a = """FREQ=HOURLY;BYDAY=MO,TU,WE,TH,FR;BYHOUR=9,10,11,12,13,14,15,16,17,18,19,20,21,22,23
# FREQ=HOURLY;BYDAY=SA,SU;BYHOUR=9,10,11,12,13,14,15,16,17,18,19,20,21,22,23"""
# aex = "FREQ=HOURLY;BYMONTH=7;BYDAY=MO,TU,WE,TH,FR;BYHOUR=9,10,11,12,13,14"
# b = rrulestr(a, forceset=True, dtstart=today)
# b.exrule(rrulestr(aex, dtstart=today, forceset=True))
# c = datetime.now(tz=tz) + relativedelta(minute=0, second=0, microsecond=0)
# today_end = today + relativedelta(days=1)
# b.between(today, today_end)
# c in b


@router.post("/klubmodul-force-resync")
async def klubmodul_force_resync(
    _: Annotated[
        list[aiosqlite.Row], Security(depends.get_current_users, scopes=["admin"])
    ],
    background_tasks: BackgroundTasks,
) -> schemas.StatusReply:
    background_tasks.add_task(refresh)
    return schemas.StatusReply(status="sync started")


@router.get("/system-status")
async def system_status(
    _: Annotated[
        list[aiosqlite.Row], Security(depends.get_current_users, scopes=["admin"])
    ],
    conn: DBcon,
):
    lsd = datetime.utcnow() - datetime.fromisoformat(
        await queries.get_last_klubmodul_sync(conn),
    )
    active_users = await queries.count_active_users(conn)
    member_access = await queries.last_log_entries(conn, limit=50)
    dt_access = []

    return {
        "last_sync": f"{lsd:%H} hours and {lsd:%M} minutes ago",
        "active_users": active_users,
        "member_access": member_access,
        "dt_access": dt_access,
        "dayticket_reception": 0,
        "dayticket_used": 0,
    }
    # last successful sync with klubmodul and number of users synced
    # return all alive?
    # last x access_log
    # estimated number of day-tickets left in reception?
