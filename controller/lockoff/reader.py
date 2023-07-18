import asyncio
import logging

from datetime import datetime
from dateutil import relativedelta
from tinydb.table import Document
import calendar
import serial_asyncio
from gpiozero import LED
from gpiozero.pins.native import NativeFactory

from .access_token import (
    TokenError,
    TokenType,
    log_and_raise_token_error,
    verify_access_token,
)
from .config import settings
from .db import DB_dayticket, DB_member
from .display import GFXDisplay

log = logging.getLogger(__name__)

# automation hat mini relay 1 is on gpio 16
factory = NativeFactory()
relay = LED(16, pin_factory=factory)


async def buzz_in():
    relay.on()
    await asyncio.sleep(5)
    relay.off()


async def opticon_reader(display: GFXDisplay):
    opticon_r, _ = await serial_asyncio.open_serial_connection(url=settings.opticon_url)
    while True:
        # read a scan from the barcode reader read until carriage return CR
        qrcode = (await opticon_r.readuntil(separator=b"\r")).decode("utf-8").strip()
        log.info(f"opticon got a qrcode with the data {qrcode}")
        async with asyncio.TaskGroup() as tg:
            try:
                user_id, token_type = verify_access_token(token=qrcode)
                # check in database
                if token_type in [TokenType.NORMAL, TokenType.MORNING]:
                    async with DB_member as db:
                        d = db.get(doc_id=user_id)
                    if not d:
                        log_and_raise_token_error(
                            "could not find user in db", code=b"F"
                        )
                    if not d["active"]:
                        log_and_raise_token_error(
                            "did you cancel your membership?", code=b"C"
                        )

                elif token_type == TokenType.DAY_TICKET_HACK:
                    async with DB_dayticket as db:
                        d = db.get(doc_id=user_id)
                    if d:
                        if datetime.utcnow() > datetime.utcfromtimestamp(d["expires"]):
                            log_and_raise_token_error("dayticket is expired", code=b"D")
                    else:
                        # expire at midnight
                        expire = datetime.now(tz=settings.tz) + relativedelta(
                            hour=23, minute=59, second=59, microsecond=0
                        )
                        db.upsert(
                            Document(
                                {"expires": calendar.timegm(expire.utctimetuple())},
                                doc_id=user_id,
                            )
                        )
                # show OK on display
                tg.create_task(display.send_message(message=b"K"))
                # buzz in
                tg.create_task(buzz_in())

            except TokenError as ex:
                # show error message on display
                tg.create_task(display.send_message(ex.code))
