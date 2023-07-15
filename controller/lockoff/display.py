import asyncio
import logging

import serial_asyncio

from .config import settings

log = logging.getLogger(__name__)

lock = asyncio.Lock()


class GFXDisplay:
    async def setup(self):
        pass
        # display_r, display_w = await serial_asyncio.open_serial_connection(
        #     url=settings.display_url
        # )
        # self.display_r = display_r
        # self.display_w = display_w

    async def runner(self):
        # send idle
        async with lock:
            log.info("display send idle message")
        #     self.display_w.write(b".")
        await asyncio.sleep(2)

    async def send_message(self, message: bytes):
        async with lock:
            pass
            log.info(f"display send message {message.decode('utf-8')}")
            # self.display_w.write(message)
