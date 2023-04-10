import asyncio
from datetime import datetime

import serial_asyncio

from . import db
from .config import settings
from .display import LCD
from .utils import TokenEnum, relay_buzz


class OpticonReader:
    def __init__(self):
        pass

    async def setup(self):
        self.r, self.w = await serial_asyncio.open_serial_connection()


async def barcode_reader():
    opticon_r, opticon_w = await serial_asyncio.open_serial_connection(
        url=settings.opticon_url
    )
    # start LCD runner
    lcd = LCD()
    await lcd.setup()
    display_task = asyncio.create_task(lcd.runner())
    while True:
        # read a scan from the barcode reader
        barcode = await opticon_r.readline()
        now = datetime.now(tz=settings.tz).replace(tzinfo=None)
        # check the last letters of the barcode in the database
        token = barcode[:8]
        query = db.tokens.select().where(db.tokens.c.token.name == token)
        # morning members allowed weekends before 12 and weekdays before 15
        if (now.weekday() in [5, 6] and now.hour < 12) or (
            now.weekday() < 5 and now.hour < 15
        ):
            query = query.where(
                db.tokens.c.token_type.in_(
                    [TokenEnum.full, TokenEnum.morning, TokenEnum.special]
                )
            )
        # else only query full members or special barcodes
        else:
            query = query.where(
                db.tokens.c.token_type.in_([TokenEnum.full, TokenEnum.special])
            )

        # if token found in database then success
        if token := await db.database.fetch_one(query):
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
                log_insert = db.access_log.insert().values(
                    token=token, timestamp=now, token_type=token.token_type
                )
                tg.create_task(db.database.execute(log_insert))
        else:
            async with asyncio.TaskGroup() as tg:
                # show error message on LCD
                lcd.queue_message(line1="access denied")
                # error sound on scanner
                opticon_w.write(b"\x1b\x45\x0d")
                # flush command to scanner
                tg.create_task(opticon_w.drain())
                # log error access in db
                log_insert = db.access_log.insert().values(
                    token=token, timestamp=now, token_type=TokenEnum.denied
                )
                tg.create_task(db.database.execute(log_insert))
