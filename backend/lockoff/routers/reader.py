import logging
from datetime import datetime, date

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException, Security, status
from fastapi.security import APIKeyHeader
from pyotp import TOTP

from .. import schemas
from ..access_token import (
    TokenError,
    TokenType,
    log_and_raise_token_error,
    verify_access_token,
)
from ..config import settings
from ..db import DB, AccessLog, Dayticket, GPass, Otherticket, User
from ..misc import DISPLAY_CODES

log = logging.getLogger(__name__)

router = APIRouter(tags=["reader"])

api_key_header = APIKeyHeader(name="reader-token", auto_error=False)


async def get_api_key(api_key_header: str = Security(api_key_header)):
    if api_key_header == settings.reader_token:
        return api_key_header
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"code": "Q", "reason": "Could not validate API KEY"},
        )


async def check_member(user_id: int, token_type: TokenType):
    today = datetime.now(tz=settings.tz)
    user = (
        await User.select(User.id)
        .where(User.id == user_id, User.active == True)
        .first()
    )
    if not user:
        log_and_raise_token_error(
            "did you cancel your membership?", code=DISPLAY_CODES.NO_MEMBER
        )
    if token_type == TokenType.OFFPEAK:
        now = datetime.now(tz=settings.tz)
        # from 10 july to 10 august offpeak members have full access
        if date(now.year, 7, 1) <= now.date() <= date(now.year, 8, 10):
            return
        # weekdays monday-thursday (friday+weekend is open for offpeak)
        if now.weekday() < 4:
            # if now.hour in [15, 16, 17, 18, 19]:  # 15:00 until 19:59 is peak?
            if now.hour >= 15:
                log_and_raise_token_error(
                    message="offpeak member outside hours",
                    code=DISPLAY_CODES.OFFPEAK_OUTSIDE_HOURS,
                )
        # weekend
        # else:
        #     if now.hour >= 12:
        #         log_and_raise_token_error(
        #             message="morning member outside hours",
        #             code=DISPLAY_CODES.OFFPEAK_OUTSIDE_HOURS,
        #         )


async def check_dayticket(user_id: int):
    if ticket := await Dayticket.select().where(Dayticket.id == user_id).first():
        if ticket["expires"] == 0:
            # first use - set expire at midnight of current day
            expire = datetime.now(tz=settings.tz) + relativedelta(
                hour=23, minute=59, second=59, microsecond=0
            )
            async with DB.transaction():
                await Dayticket.update(
                    {Dayticket.expires: int(expire.timestamp())}
                ).where(Dayticket.id == user_id)
        elif datetime.now(tz=settings.tz) > datetime.fromtimestamp(
            ticket["expires"], tz=settings.tz
        ):
            log_and_raise_token_error(
                "dayticket is expired", code=DISPLAY_CODES.DAYTICKET_EXPIRED
            )
    else:
        log_and_raise_token_error(
            "no such dayticket!?", code=DISPLAY_CODES.DAYTICKET_EXPIRED
        )


async def check_totp(user_id: int, totp: str):
    gps = await GPass.select(GPass.totp).where(GPass.user_id == user_id)
    verifiers = [TOTP(s=gp["totp"], digits=8) for gp in gps]
    if not any([verifier.verify(otp=totp, valid_window=5) for verifier in verifiers]):
        log_and_raise_token_error(
            "totp code did not match", code=DISPLAY_CODES.QR_ERROR_SIGNATURE
        )


async def check_otherticket(user_id: int):
    ticket = (
        await Otherticket.select(Otherticket.id)
        .where(Otherticket.id == user_id)
        .first()
    )
    if not ticket:
        log_and_raise_token_error("no such ticket", code=DISPLAY_CODES.NO_MEMBER)


async def check_qrcode(qr_code: str) -> tuple[int, str, str]:
    user_id, token_type, token_media, totp = verify_access_token(
        token=qr_code
    )  # it will raise TokenError if not valid
    log.info(f"checking user {user_id} {token_type} {totp}")
    # check in database
    match token_type:
        case (
            TokenType.NORMAL
            | TokenType.OFFPEAK
            | TokenType.JUNIOR_HOLD
            | TokenType.BØRNE_HOLD
        ):
            await check_member(user_id=user_id, token_type=token_type)
            if totp:
                await check_totp(user_id=user_id, totp=totp)
        case TokenType.DAY_TICKET:
            await check_dayticket(user_id=user_id)
        case TokenType.OTHER:
            await check_otherticket(user_id=user_id)
        case _:
            log_and_raise_token_error("general error", code=DISPLAY_CODES.GENERIC_ERROR)
    log.info(f"{user_id} {token_type} access granted")
    # log in access_log db
    async with DB.transaction():
        await AccessLog.insert(
            AccessLog(
                id=None,
                obj_id=user_id,
                token_type=token_type,
                token_media=token_media,
                timestamp=datetime.now(tz=settings.tz).isoformat(timespec="seconds"),
            )
        )
    return (user_id, token_type, token_media)


@router.post("/reader-check-code", dependencies=[Depends(get_api_key)])
async def reader_check_code(data: schemas.ReaderCheckCode):
    try:
        user_id, _, _ = await check_qrcode(qr_code=data.qr_code)
    except TokenError as ex:
        raise HTTPException(
            status_code=status.HTTP_418_IM_A_TEAPOT,
            detail={"code": ex.code.decode(), "reason": str(ex)},
        )
    return schemas.StatusReply(status="J" if user_id in settings.eljefe else "K")
