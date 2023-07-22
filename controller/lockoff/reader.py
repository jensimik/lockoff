import asyncio
import calendar
import logging
import asyncio
from datetime import datetime

import aiosqlite
import serial_asyncio
from dateutil import relativedelta
from gpiozero import LED

from .access_token import (
    TokenError,
    TokenType,
    log_and_raise_token_error,
    verify_access_token,
)
from .config import settings
from .misc import GFXDisplay, queries

log = logging.getLogger(__name__)

# automation hat mini relay 1 is on gpio pin 16
relay = LED(16)


class OPTICON_CMD:
    OK = bytes([0x1B, 0x42, 0x4C, 0xD])  # sound ok and led ok
    ERROR = bytes([0x1B, 0x45, 0xD])  # sound error


async def buzz_in():
    relay.on()
    await asyncio.sleep(4)
    relay.off()


async def check_member(
    user_id: int, member_type: TokenType, conn: aiosqlite.Connection
):
    user = await queries.get_active_user_by_user_id(conn, user_id=user_id)
    if not user:
        log_and_raise_token_error("did you cancel your membership?", code=b"C")
    if member_type == TokenType.MORNING:
        # TODO: check if morning member has access in current hour?
        pass


async def check_dayticket_hack(user_id: int, conn: aiosqlite.Connection):
    if ticket := await queries.get_dayticket_by_id(conn, ticket_id=user_id):
        if datetime.utcnow() > datetime.utcfromtimestamp(ticket["expires"]):
            log_and_raise_token_error("dayticket is expired", code=b"D")
    else:
        # expire at midnight
        expire = datetime.now(tz=settings.tz) + relativedelta(
            hour=23, minute=59, second=59, microsecond=0
        )
        await queries.update_dayticket_expire(
            conn,
            ticket_id=user_id,
            expires=calendar.timegm(expire.utctimetuple()),
        )


async def check_qrcode(qr_code: str):
    async with aiosqlite.connect(settings.db_file) as conn:
        conn.row_factory = aiosqlite.Row
        user_id, token_type = verify_access_token(
            token=qr_code
        )  # it will raise TokenError if not valid
        log.info(f"checking user {user_id} {token_type}")
        # check in database
        match token_type:
            case TokenType.NORMAL | TokenType.MORNING:
                await check_member(user_id=user_id, member_type=token_type, conn=conn)
            case TokenType.DAY_TICKET_HACK:
                await check_dayticket_hack(user_id=user_id, conn=conn)
        log.info(f"{user_id} {token_type} access granted")
        # log in access_log db
        await queries.log_entry(
            conn,
            user_id=user_id,
            token_type=token_type.name,
            timestamp=datetime.utcnow().isoformat(timespec="seconds"),
        )
        await conn.commit()


async def opticon_reader(display: GFXDisplay):
    opticon_r, opticon_w = await serial_asyncio.open_serial_connection(
        url=settings.opticon_url
    )
    # TODO: should i send opticon configuration by serial to ensure it is correct before starting?
    while True:
        # read a scan from the barcode reader read until carriage return CR
        qr_code = (await opticon_r.readuntil(separator=b"\r")).decode("utf-8").strip()
        async with asyncio.TaskGroup() as tg:
            try:
                await check_qrcode(qr_code)
                # buzz in
                tg.create_task(buzz_in())
                # show OK on display
                tg.create_task(display.send_message(message=b"K"))
                # give good sound on opticon now qr code is verified
                opticon_w.write(OPTICON_CMD.OK)
                tg.create_task(opticon_w.drain())
            except TokenError as ex:
                # show error message on display
                log.warning(ex)
                tg.create_task(display.send_message(ex.code))
                opticon_w.write(OPTICON_CMD.ERROR)
                tg.create_task(opticon_w.drain())
            # generic error? show system error on display
            except Exception:
                log.exception("generic error in reader")
                tg.create_task(display.send_message(b"E"))
                opticon_w.write(OPTICON_CMD.ERROR)
                tg.create_task(opticon_w.drain())
