import asyncio
import logging

import serial_asyncio

from .config import settings

log = logging.getLogger(__name__)

lock = asyncio.Lock()


class GFXDisplay:
    async def setup(self):
        _, display_w = await serial_asyncio.open_serial_connection(
            url=settings.display_url
        )
        self.display_w = display_w

    async def runner(self):
        # send idle
        while True:
            async with lock:
                if settings.display_url:
                    self.display_w.write(b".")
                else:
                    log.info("display send idle message")
            await asyncio.sleep(1.5)

    async def send_message(self, message: bytes):
        async with lock:
            if settings.display_url:
                self.display_w.write(message)
            else:
                log.info(f"display send message {message.decode('utf-8')}")
