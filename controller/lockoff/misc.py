import asyncio
import hashlib
import logging
import pathlib
from datetime import datetime

import aiosql
import serial_asyncio
from contextlib import asynccontextmanager

import aiosqlite
from fastapi import FastAPI
import redis.asyncio as redis
from fastapi_limiter import FastAPILimiter
from .klubmodul import klubmodul_runner
from .misc import GFXDisplay, Watchdog, queries
from .reader import opticon_reader

from .config import settings

log = logging.getLogger(__name__)
lock = asyncio.Lock()
module_directory = pathlib.Path(__file__).resolve().parent
queries = aiosql.from_path(module_directory / "queries.sql", "aiosqlite")
watchdog = Watchdog()


def simple_hash(data: str) -> str:
    return hashlib.sha256(f"{data}{settings.hash_salt}".encode()).hexdigest()


@asynccontextmanager
async def lifespan(app: FastAPI):
    _redis = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(_redis)
    async with aiosqlite.connect(settings.db_file) as conn:
        await queries.create_schema(conn)
        await conn.commit()
    if settings.prod:
        # start display
        display = GFXDisplay()
        await display.setup()
        display_task = asyncio.create_task(display.runner())
        watchdog.watch(display_task)
        # start opticon reader
        opticon_task = asyncio.create_task(opticon_reader(display=display))
        watchdog.watch(opticon_task)
        # start klubmodul runner
        klubmodul_task = asyncio.create_task(klubmodul_runner())
        watchdog.watch(klubmodul_task)
    yield
    # clear things now at shutdown
    # nothing really have to be cleared


class GFXDisplay:
    async def setup(self, url=settings.display_url):
        _, display_w = await serial_asyncio.open_serial_connection(url=url)
        self.display_w = display_w

    async def runner(self):
        # send idle
        while True:
            now = datetime.now(tz=settings.tz)
            async with lock:
                if settings.display_url:
                    # show screensaver at nightime idle
                    if now.hour < 7:
                        self.display_w.write(b",")
                    else:
                        self.display_w.write(b".")
                    await self.display_w.drain()
                else:
                    log.info("display send idle message")
            await asyncio.sleep(1.5)

    async def send_message(self, message: bytes):
        async with lock:
            if settings.display_url:
                self.display_w.write(message)
                await self.display_w.drain()
            else:
                log.info(f"display send message {message.decode('utf-8')}")


class Watchdog:
    def __init__(self):
        self._watch = []

    def watch(self, watch: asyncio.Task):
        self._watch.append(watch)

    def healthy(self):
        if any([w.done() for w in self._watch]):
            return False
        return True
