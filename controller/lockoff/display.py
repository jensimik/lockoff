import asyncio
import logging

import serial_asyncio

from .config import settings

log = logging.getLogger(__name__)

lock = asyncio.Lock()


class GFXDisplay:
    async def setup(self):
        display_r, display_w = await serial_asyncio.open_serial_connection(
            url=settings.display_url
        )
        self.display_r = display_r
        self.display_w = display_w

    async def runner(self):
        # send idle
        async with lock:
            self.display_w.write(b".")
        asyncio.sleep(2)

    async def send_message(self, message: bytes):
        async with lock:
            self.display_w.write(message)
