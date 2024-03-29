import io
import logging
import asyncio
from datetime import datetime, date
from typing import Annotated
import itertools
import statistics

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
    TokenError,
    TokenMedia,
    TokenType,
    generate_access_token,
    generate_dl_admin_token,
    verify_access_token,
    verify_dl_admin_token,
)
from ..card import generate_png, GooglePass, GPassStatus, AppleNotifier
from ..config import settings
from ..db import (
    DB,
    AccessLog,
    Dayticket,
    Max,
    Otherticket,
    User,
    UserModel,
    GPass,
    APDevice,
    APPass,
    APReg,
)
from ..klubmodul import refresh

router = APIRouter(tags=["admin"])

log = logging.getLogger(__name__)


@router.post("/daytickets")
async def generate_daytickets(
    pages_to_print: schemas.PagesToPrint,
    _: Annotated[
        list[UserModel], Security(depends.get_current_users, scopes=["admin"])
    ],
):
    batch_id = datetime.now(tz=settings.tz).isoformat(timespec="seconds")
    async with DB.transaction():
        dayticket_ids = [
            (
                await Dayticket.insert(Dayticket(id=None, batch_id=batch_id)).returning(
                    Dayticket.id
                )
            )[0]["id"]
            for _ in range(30 * pages_to_print.pages_to_print)
        ]
    return [
        {
            "dayticket_id": dayticket_id,
            "dl_token": generate_dl_admin_token(user_id=dayticket_id),
        }
        for dayticket_id in dayticket_ids
    ]


@router.get(
    "/daytickets/{token}/qr-code.png",
    response_class=Response,
    responses={
        200: {"content": {"image/png": {}}},
    },
)
async def get_qr_code_png(
    ticket_id: Annotated[int, Depends(verify_dl_admin_token)],
):
    log.info(f"getting qr code for ticket_id {ticket_id}")
    ticket = await Dayticket.select().where(Dayticket.id == ticket_id)
    if not ticket:
        log.error(f"could not find ticket with id {ticket_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    access_token = generate_access_token(
        user_id=ticket_id,
        token_type=TokenType.DAY_TICKET,
        token_media=TokenMedia.PRINT,
        expire_delta=relativedelta(months=12),
    )
    img = generate_png(qr_code_data=access_token.decode())
    with io.BytesIO() as f:
        img.save(f, format="png")
        content = f.getvalue()
    return Response(content=content, media_type="image/png")


@router.get(
    "/othertickets/{token}/qr-code.png",
    response_class=Response,
    responses={
        200: {"content": {"image/png": {}}},
    },
)
async def get_qr_code_png(
    ticket_id: Annotated[int, Depends(verify_dl_admin_token)],
):
    log.info(f"getting qr code for ticket_id {ticket_id}")
    ticket = await Otherticket.select().where(Otherticket.id == ticket_id)
    if not ticket:
        log.error(f"could not find ticket with id {ticket_id}")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    access_token = generate_access_token(
        user_id=ticket_id,
        token_type=TokenType.OTHER,
        token_media=TokenMedia.PRINT,
        expire_delta=relativedelta(months=48),
    )
    img = generate_png(qr_code_data=access_token.decode())
    with io.BytesIO() as f:
        img.save(f, format="png")
        content = f.getvalue()
    return Response(content=content, media_type="image/png")


@router.get("/othertickets")
async def get_other_tickets(
    _: Annotated[
        list[UserModel], Security(depends.get_current_users, scopes=["admin"])
    ],
):
    tickets = await Otherticket.select().where(Otherticket.active == True)
    return tickets


@router.post("/othertickets")
async def create_other_ticket(
    data: schemas.OtherTicket,
    _: Annotated[
        list[UserModel], Security(depends.get_current_users, scopes=["admin"])
    ],
):
    inserted = await Otherticket.insert(
        Otherticket(id=None, name=data.name, active=True)
    ).returning(Otherticket.id)


@router.get("/othertickets/{id}")
async def get_other_tickets(
    id: int,
    _: Annotated[
        list[UserModel], Security(depends.get_current_users, scopes=["admin"])
    ],
):
    ticket = Otherticket.select().where(Otherticket.id == id)
    ticket["dl_token"] = generate_dl_admin_token(user_id=ticket["id"])
    return ticket


@router.delete("/othertickets/{id}")
async def delete_other_ticket(
    id: int,
    _: Annotated[
        list[UserModel], Security(depends.get_current_users, scopes=["admin"])
    ],
) -> schemas.StatusReply:
    await Otherticket.update({Otherticket.active: False}).where(Otherticket.id == id)
    return schemas.StatusReply(status="OK")


@router.post("/check-token")
async def check_token(
    token_input: schemas.TokenCheckInput,
    _: Annotated[
        list[UserModel], Security(depends.get_current_users, scopes=["admin"])
    ],
) -> schemas.TokenCheck:
    try:
        user_id, token_type, _, totp = verify_access_token(token=token_input.token)
        name = "n/a"
    except TokenError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="could not verify signature - is it a nkk qr code?",
        )
    match token_type:
        case TokenType.NORMAL | TokenType.OFFPEAK:
            user = (
                await User.select(User.name, User.active, User.token_type)
                .where(User.id == user_id)
                .first()
            )
            name = user["name"]
            if not user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="user not found"
                )
            elif not user["active"]:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST, detail="user not active"
                )
            if token_type == TokenType.OFFPEAK:
                # TODO: do check for hours?
                pass
        case TokenType.DAY_TICKET:
            ticket = (
                await Dayticket.select(Dayticket.id, Dayticket.expires)
                .where(Dayticket.id == user_id)
                .first()
            )
            if not ticket:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="dayticket not found!?",
                )
            match ticket["expires"]:
                case _ as expires if expires == 0:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="dayticket has not been activated yet",
                    )
                case _ as expires if expires > 0:
                    expires = datetime.fromtimestamp(ticket["expires"], tz=settings.tz)
                    if expires < datetime.now(tz=settings.tz):
                        raise HTTPException(
                            status_code=status.HTTP_400_BAD_REQUEST,
                            detail=f"dayticket is expired {expires}",
                        )
        case TokenType.OTHER:
            ticket = await Otherticket.select(Otherticket.id).where(
                Otherticket.id == user_id, Otherticket.active == True
            )
            if not ticket:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="ticket not found or inactive",
                )
    return schemas.TokenCheck(user_id=user_id, token_type=token_type.name, name=name)


@router.post("/klubmodul-force-resync")
async def klubmodul_force_resync(
    _: Annotated[
        list[UserModel], Security(depends.get_current_users, scopes=["admin"])
    ],
    background_tasks: BackgroundTasks,
) -> schemas.StatusReply:
    background_tasks.add_task(refresh)
    return schemas.StatusReply(status="sync started")


async def expire_google_passes_task():
    google_passes = await GPass.select().where(GPass.status != GPassStatus.DELETED)
    async with GooglePass() as gp:
        for p in google_passes:
            try:
                pass_id = p["id"]
                return_code = "OK" if await gp.expire_pass(pass_id=pass_id) else "FAIL"
                log.info(f"expired pass with id {pass_id} {return_code}")
                await asyncio.sleep(2)
            except Exception as ex:
                log.exception(f"failed with {ex}")


@router.delete("/expire-all-google-passes")
async def expire_google_passes(
    _: Annotated[
        list[UserModel], Security(depends.get_current_users, scopes=["admin"])
    ],
    background_tasks: BackgroundTasks,
) -> schemas.StatusReply:
    background_tasks.add_task(expire_google_passes_task)
    return schemas.StatusReply(status="done")


async def expire_apple_passes_task():
    async with AppleNotifier() as apn:
        passes = await APPass.select()  # .where(APPass.user_id == 3587)
        for p in passes:
            async with DB.transaction():
                await APPass.update({APPass.update_tag: APPass.update_tag + 1}).where(
                    APPass.id == p["id"]
                )
            for r in await APReg.select().where(APReg.serial_number == p["id"]):
                device = (
                    await APDevice.select(APDevice.push_token)
                    .where(APDevice.id == r["device_library_identifier"])
                    .first()
                )
                push_token = device["push_token"]
                log.info(f"requested update of push token {push_token}")
                await apn.notify_update(push_token=push_token)
                await asyncio.sleep(2)


@router.delete("/expire-all-apple-passes")
async def expire_apple_passes(
    _: Annotated[
        list[UserModel], Security(depends.get_current_users, scopes=["admin"])
    ],
    background_tasks: BackgroundTasks,
) -> schemas.StatusReply:
    background_tasks.add_task(expire_apple_passes_task)
    return schemas.StatusReply(status="done")


@router.get("/log-raw.json")
async def get_raw_log(
    _: Annotated[
        list[UserModel], Security(depends.get_current_users, scopes=["admin"])
    ],
):
    data = await AccessLog.select().order_by(AccessLog.timestamp, ascending=False)
    return {"data": data}


@router.get("/log-unique-daily.json")
async def get_log_unique_daily(
    _: Annotated[
        list[UserModel], Security(depends.get_current_users, scopes=["admin"])
    ],
):
    data = []
    rawdata = await AccessLog.select().order_by(AccessLog.timestamp)
    for k, g in itertools.groupby(rawdata, lambda x: x["timestamp"][:10]):
        d = date.fromisoformat(k)
        row = {"day": k, "dow": f"{d:%A}".lower()}
        lg = list(g)
        for tt in TokenType:
            row[tt.name] = len(
                {x["obj_id"] for x in lg if TokenType(x["token_type"]) == tt}
            )
        data.append(row)
    return {"data": sorted(data, key=lambda x: x["day"], reverse=True)}


@router.get("/log-user-freq.json")
async def get_log_user_freq(
    _: Annotated[
        list[UserModel], Security(depends.get_current_users, scopes=["admin"])
    ],
):
    data = []
    rawdata = (
        await AccessLog.select()
        .where(
            AccessLog.token_type.is_in(
                [TokenType.NORMAL.value, TokenType.OFFPEAK.value]
            )
        )
        .order_by(AccessLog.obj_id)
    )
    for user_id, g in itertools.groupby(rawdata, lambda x: x["obj_id"]):
        lg = list(g)
        dates = sorted({date.fromisoformat(x["timestamp"][:10]) for x in lg})
        diffs = [(x2 - x1).days for (x1, x2) in itertools.pairwise(dates)]
        if diffs:
            data.append(
                {"user_id": user_id, "median_freq": round(statistics.median(diffs), 2)}
            )
    return {"data": data}


@router.get("/system-status")
async def system_status(
    _: Annotated[
        list[UserModel], Security(depends.get_current_users, scopes=["admin"])
    ],
):
    last_batch_id = (
        await User.select(Max(User.batch_id).as_alias("last_batch_id"))
        .where(User.active == True)
        .first()
    )["last_batch_id"]
    lsd = datetime.now(tz=settings.tz) - datetime.fromisoformat(last_batch_id)
    hours, remainder = divmod(lsd.total_seconds(), 3600)
    minutes, _ = divmod(remainder, 60)
    active_users = await User.count().where(User.active == True)
    member_access = (
        await AccessLog.select()
        .order_by(AccessLog.timestamp, ascending=False)
        .limit(20)
    )
    # fixup display of tokentype and tokenmedia
    for ma in member_access:
        ma["token_type"] = TokenType(ma["token_type"]).name
        ma["token_media"] = TokenMedia(ma["token_media"]).name
    dt_stats = await Dayticket.raw(
        """
SELECT batch_id,
min(dayticket.id) as range_start,
max(dayticket.id) as range_end, 
SUM(CASE WHEN expires = 0 THEN 1 ELSE 0 END) as unused,
SUM(CASE WHEN expires > 0 THEN 1 ELSE 0 END) as used
from dayticket
group by batch_id"""
    )
    ft_stats = (
        await Otherticket.select()
        .where(Otherticket.active == True)
        .order_by(Otherticket.name)
    )
    for ft in ft_stats:
        ft["dl_token"] = generate_dl_admin_token(user_id=ft["id"])
    dayticket_reception = await Dayticket.count().where(Dayticket.expires == 0)
    dayticket_used = await Dayticket.count().where(Dayticket.expires > 0)
    digital_issued = await User.count().where(
        User.season_digital == str(settings.current_season)
    )
    print_issued = await User.count().where(
        User.season_print == str(settings.current_season)
    )
    total_issued = await User.count().where(
        (User.season_print == str(settings.current_season))
        | (User.season_digital == str(settings.current_season))
    )
    return {
        "last_sync": f"{hours:.0f} hours and {minutes:.0f} minutes ago",
        "active_users": active_users,
        "member_access": member_access,
        "dt_stats": dt_stats,
        "fixed_tickets": ft_stats,
        "dayticket_reception": dayticket_reception,
        "dayticket_used": dayticket_used,
        "digital_issued": digital_issued,
        "print_issued": print_issued,
        "total_issued": total_issued,
    }
