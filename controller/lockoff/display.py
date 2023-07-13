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
        # send idle and expect ack
        async with lock:
            self.display_w.write(b".")
            ack = await self.display_r.readexactly(1)
            if ack != "#":
                raise Exception("not correct ack")
        asyncio.sleep(2)

    async def send_message(self, message):
        async with lock:
            self.display_w.write(message.encode("utf-8"))
            ack = await self.display_r.readexactly(1)
            if ack != "#":
                raise Exception("not correct ack")
