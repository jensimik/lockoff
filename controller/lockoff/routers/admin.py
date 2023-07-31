import io
import logging
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

log = logging.getLogger(__name__)


@router.post("/generate-daytickets")
async def klubmodul_force_resync(
    pages_to_print: schemas.PagesToPrint,
    _: Annotated[
        list[aiosqlite.Row], Security(depends.get_current_users, scopes=["admin"])
    ],
    conn: DBcon,
):
    batch_id = datetime.now(tz=settings.tz).isoformat(timespec="seconds")
    dayticket_ids = [
        await queries.insert_dayticket(conn, batch_id=batch_id)
        for _ in range(30 * pages_to_print)
    ]
    await conn.commit()
    return [
        {
            "dayticket_id": dayticket_id,
            "dl_token": generate_dl_token(user_id=dayticket_id),
        }
        for dayticket_id in dayticket_ids
    ]


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
    log.info("getting qr code for ticket_id {ticket_id}")
    ticket = await queries.get_dayticket_by_id(conn, ticket_id=ticket_id)
    if not ticket:
        log.error("could not find ticket with id {ticket_id}")
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
    lsd = datetime.now(tz=settings.tz) - datetime.fromisoformat(
        await queries.get_last_klubmodul_sync(conn),
    )
    hours, remainder = divmod(lsd.total_seconds(), 3600)
    minutes, _ = divmod(remainder, 60)
    active_users = await queries.count_active_users(conn)
    member_access = await queries.last_log_entries(conn, limit=50)
    dt_stats = await queries.get_dayticket_stats(conn)
    dayticket_reception = sum([d["unused"] for d in dt_stats])
    dayticket_used = sum([d["used"] for d in dt_stats])
    return {
        "last_sync": f"{hours:.0f} hours and {minutes:.0f} minutes ago",
        "active_users": active_users,
        "member_access": member_access,
        "dt_stats": dt_stats,
        "dayticket_reception": dayticket_reception,
        "dayticket_used": dayticket_used,
    }
