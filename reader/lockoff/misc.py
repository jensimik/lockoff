import asyncio
import logging
import pathlib
from datetime import datetime

import serial_asyncio
from gpiozero import LED

from .config import settings

log = logging.getLogger(__name__)
lock = asyncio.Lock()
module_directory = pathlib.Path(__file__).resolve().parent
# automation hat mini relay 1 is on gpio pin 16
relay = LED(16)


class DISPLAY_CODES:
    OK = b"K"
    GENERIC_ERROR = b"E"
    DAYTICKET_EXPIRED = b"D"
    NO_MEMBER = b"C"
    QR_ERROR = b"Q"
    QR_ERROR_SIGNATURE = b"S"
    QR_ERROR_EXPIRED = b"X"


class O_CMD:
    OK_SOUND = bytes([0x1B, 0x42, 0xD])
    OK_LED = bytes([0x1B, 0x4C, 0xD])
    ERROR_SOUND = bytes([0x1B, 0x45, 0xD])
    ERROR_LED = bytes([0x1B, 0x4E, 0xD])
    TRIGGER = bytes([0x1B, 0x5A, 0xD])
    DETRIGGER = bytes([0x1B, 0x59, 0xD])


async def buzz_in(sleep: int = 4):
    print("buzzing in")
    relay.on()
    await asyncio.sleep(sleep)
    relay.off()


class Watchdog:
    def __init__(self):
        self._watch = []

    def watch(self, watch: asyncio.Task):
        self._watch.append(watch)

    def healthy(self):
        if any([w.done() for w in self._watch]):
            return False
        return True


watchdog = Watchdog()


class GFXDisplay:
    async def setup(self, url=settings.display_url):
        _, display_w = await serial_asyncio.open_serial_connection(url=url)
        self.display_w = display_w

    async def runner(self, one_time_run: bool = False):
        # send idle
        while True:
            now = datetime.now(tz=settings.tz)
            async with lock:
                # show screensaver at nightime idle
                if now.hour < 7:
                    self.display_w.write(b",")
                else:
                    self.display_w.write(b".")
                await self.display_w.drain()
            if one_time_run:
                break
            await asyncio.sleep(1.5)

    async def send_message(self, message: bytes):
        async with lock:
            log.info(f"display send message {message.decode('utf-8')}")
            self.display_w.write(message)
            await self.display_w.drain()
