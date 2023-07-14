import asyncio
import logging

import serial_asyncio

from .access_token import TokenError, verify_access_token
from .config import settings
from .display import GFXDisplay

log = logging.getLogger(__name__)


async def opticon_reader(display: GFXDisplay):
    opticon_r, _ = await serial_asyncio.open_serial_connection(url=settings.opticon_url)
    while True:
        # read a scan from the barcode reader
        qrcode = await opticon_r.readline()
        log.info(f"i got a qrcode with the data {qrcode}")
        try:
            if user_id := await verify_access_token(token=qrcode):
                log.info(f"successful verified the qrcode as user_id: {user_id}")
                asyncio.create_task(
                    display.send_message(message=b"K")
                )  # send OK signal
                # buzz person in test
                log.info("buzzing relay")
                # await relay_open()
                await asyncio.sleep(5)
                # await relay_close()
        except TokenError as ex:
            async with asyncio.TaskGroup() as tg:
                # TODO: show correct error message on display?
                tg.create_task(display.send_message(b"Q"))
