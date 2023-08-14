import asyncio
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import FastAPI
from fastapi_limiter import FastAPILimiter
from piccolo.table import create_db_tables

from .card import GooglePass
from .config import settings
from .db import AccessLog, APDevice, APPass, APReg, Dayticket, GPass, User
from .klubmodul import klubmodul_runner
from .misc import GFXDisplay, watchdog
from .reader import Reader


@asynccontextmanager
async def lifespan(app: FastAPI):
    _redis = redis.from_url(settings.redis_url, encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(_redis)
    # init db and create tables if not exists
    await create_db_tables(
        User, Dayticket, AccessLog, APReg, APDevice, APPass, GPass, if_not_exists=True
    )
    # start display
    display = GFXDisplay()
    await display.setup()
    display_task = asyncio.create_task(display.runner())
    watchdog.watch(display_task)
    # start opticon reader
    reader = Reader()
    await reader.setup(display=display)
    opticon_task = asyncio.create_task(reader.runner())
    watchdog.watch(opticon_task)
    # start klubmodul runner
    klubmodul_task = asyncio.create_task(klubmodul_runner())
    watchdog.watch(klubmodul_task)
    # assure google-wallet class is created
    async with GooglePass() as gp:
        await gp.create_class()
    yield
    # clear things now at shutdown
    # nothing really have to be cleared
