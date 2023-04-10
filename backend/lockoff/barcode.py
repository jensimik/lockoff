import asyncio
import logging
from datetime import datetime

import serial_asyncio

from . import db
from .config import settings
from .display import LCD
from .utils import TokenEnum, relay_buzz

log = logging.getLogger(__name__)


class OpticonReader:
    def __init__(self):
        pass

    async def setup(self):
        self.r, self.w = await serial_asyncio.open_serial_connection()


async def barcode_reader(lcd: LCD):
    opticon_r, opticon_w = await serial_asyncio.open_serial_connection(
        url=settings.opticon_url
    )
    while True:
        # read a scan from the barcode reader
        barcode = await opticon_r.readline()
        now = datetime.now(tz=settings.tz).replace(tzinfo=None)
        # check the last letters of the barcode in the database
        token_str = barcode[:8]
        entry_granted, token = await db.check_token(token=token_str, now=now)
        if entry_granted:
            async with asyncio.TaskGroup() as tg:
                # buzz person in
                tg.create_task(relay_buzz())
                # show success message on LCD
                lcd.queue_message(
                    line1=f"hej {token.name[:10]}",
                    line2=token.token_type.name,
                )
                # success sound on scanner
                opticon_w.write(b"\x1b\x42\x0d")
                # success led on scanner
                opticon_w.write(b"\x1b\x4c\x0d")
                # flush commands to scanner
                tg.create_task(opticon_w.drain())
                # log access in database
                tg.create_task(
                    db.access_log(
                        token=token_str, timestamp=now, token_type=token.token_type
                    )
                )
        else:
            async with asyncio.TaskGroup() as tg:
                # show error message on LCD
                lcd.queue_message(line1="access denied")
                # error sound on scanner
                opticon_w.write(b"\x1b\x45\x0d")
                # flush command to scanner
                tg.create_task(opticon_w.drain())
                # log error access in db
                tg.create_task(
                    db.access_log(
                        token=token_str, timestamp=now, token_type=TokenEnum.denied
                    )
                )
