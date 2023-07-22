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


async def buzz_in():
    relay.on()
    await asyncio.sleep(5)
    relay.off()


async def opticon_reader(display: GFXDisplay):
    opticon_r, _ = await serial_asyncio.open_serial_connection(url=settings.opticon_url)
    while True:
        async with aiosqlite.connect(settings.db_file) as conn:
            conn.row_factory = aiosqlite.Row
            # read a scan from the barcode reader read until carriage return CR
            qrcode = (
                (await opticon_r.readuntil(separator=b"\r")).decode("utf-8").strip()
            )
            async with asyncio.TaskGroup() as tg:
                try:
                    user_id, token_type = verify_access_token(token=qrcode)
                    log.info(f"checking user {user_id} {token_type}")
                    # check in database
                    if token_type in [TokenType.NORMAL, TokenType.MORNING]:
                        user = await queries.get_user_by_user_id(conn, user_id=user_id)
                        if not user:
                            log_and_raise_token_error(
                                "could not find user in db", code=b"F"
                            )
                        if not user["active"]:
                            log_and_raise_token_error(
                                "did you cancel your membership?", code=b"C"
                            )
                    elif token_type == TokenType.MORNING:
                        # TODO: check if morning member can still get in?
                        pass

                    elif token_type == TokenType.DAY_TICKET_HACK:
                        ticket = await queries.get_dayticket_by_id(
                            conn, ticket_id=user_id
                        )
                        if ticket:
                            if datetime.utcnow() > datetime.utcfromtimestamp(
                                ticket["expires"]
                            ):
                                log_and_raise_token_error(
                                    "dayticket is expired", code=b"D"
                                )
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
                    log.info(f"{user_id} {token_type} access granted")
                    await queries.log_entry(
                        conn,
                        user_id=user_id,
                        token_type=token_type.name,
                        timestamp=datetime.utcnow().isoformat(timespec="seconds"),
                    )
                    # show OK on display
                    tg.create_task(display.send_message(message=b"K"))
                    # buzz in
                    tg.create_task(buzz_in())
                    await conn.commit()

                except TokenError as ex:
                    # show error message on display
                    log.error(ex)
                    tg.create_task(display.send_message(ex.code))
                # generic error? show system error on display
                except Exception:
                    log.exception("generic error in reader")
                    tg.create_task(display.send_message(b"E"))
