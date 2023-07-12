import asyncio
import logging

import serial_asyncio

from .access_token import TokenError, verify_access_token
from .config import settings

log = logging.getLogger(__name__)


async def opticon_reader():
    opticon_r, _ = await serial_asyncio.open_serial_connection(url=settings.opticon_url)
    while True:
        # read a scan from the barcode reader
        qrcode = await opticon_r.readline()
        log.info(f"i got a qrcode with the data {qrcode}")
        try:
            if user_id := await verify_access_token(token=qrcode):
                log.info(f"successful verified the qrcode as user_id: {user_id}")
                # buzz person in test
                log.info("buzzing relay")
                # await relay_open()
                await asyncio.sleep(5)
                # await relay_close()
        except TokenError as ex:
            async with asyncio.TaskGroup() as tg:
                pass
                # TODO: show error message on display?
