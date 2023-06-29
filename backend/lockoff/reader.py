import asyncio
import logging
from datetime import datetime

import serial_asyncio

from .access_token import verify_access_token, TokenError
from .config import settings

log = logging.getLogger(__name__)


async def opticon_reader():
    opticon_r, _ = await serial_asyncio.open_serial_connection(url=settings.opticon_url)
    while True:
        # read a scan from the barcode reader
        qrcode = await opticon_r.readline()
        log.info(f"i got a qrcode with the data {qrcode}")
        now = datetime.now(tz=settings.tz).replace(tzinfo=None)
        # check the last letters of the barcode in the database
        try:
            if user_id := await verify_access_token(token=qrcode):
                log.info(f"successful verified the qrcode as user_id: {user_id}")
                # buzz person in
                log.info("buzzing relay")
                # await relay_open()
                await asyncio.sleep(5)
                # await relay_close()
        except TokenError as ex:
            async with asyncio.TaskGroup() as tg:
                pass
