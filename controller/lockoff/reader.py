import asyncio
import calendar
import logging
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


class O_CMD:
    OK_SOUND = bytes([0x1B, 0x42, 0xD])
    OK_LED = bytes([0x1B, 0x4C, 0xD])
    ERROR_SOUND = bytes([0x1B, 0x45, 0xD])
    ERROR_LED = bytes([0x1B, 0x4E, 0xD])


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


async def opticon_cmd(writer: asyncio.StreamWriter, cmds=list[bytes]):
    for cmd in cmds:
        writer.write(cmd)
    await writer.drain()


async def opticon_reader(display: GFXDisplay):
    _r, _w = await serial_asyncio.open_serial_connection(url=settings.opticon_url)
    # TODO: should i send opticon configuration by serial to ensure it is correct before starting?
    while True:
        # read a scan from the barcode reader read until carriage return CR
        qr_code = (await _r.readuntil(separator=b"\r")).decode("utf-8").strip()
        async with asyncio.TaskGroup() as tg:
            try:
                await check_qrcode(qr_code)
                # buzz in
                tg.create_task(buzz_in())
                # show OK on display
                tg.create_task(display.send_message(message=b"K"))
                # give good sound on opticon now qr code is verified
                tg.create_task(opticon_cmd(_w, [O_CMD.OK_SOUND, O_CMD.OK_LED]))
            except TokenError as ex:
                # show error message on display
                log.warning(ex)
                tg.create_task(display.send_message(ex.code))
                tg.create_task(_w, [O_CMD.ERROR_SOUND, O_CMD.ERROR_LED])
            # generic error? show system error on display
            except Exception:
                log.exception("generic error in reader")
                tg.create_task(display.send_message(b"E"))
                tg.create_task(_w, [O_CMD.ERROR_SOUND, O_CMD.ERROR_LED])
