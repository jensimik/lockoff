import asyncio
from contextlib import asynccontextmanager

import aiosqlite
import redis.asyncio as redis
from fastapi import FastAPI
from fastapi_limiter import FastAPILimiter

from .config import settings
from .klubmodul import klubmodul_runner
from .misc import GFXDisplay, Watchdog, queries
from .reader import opticon_reader

watchdog = Watchdog()


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
