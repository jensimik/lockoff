import asyncio
import logging
from contextlib import asynccontextmanager

import aiosqlite
import redis.asyncio as redis
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

from .config import settings
from .klubmodul import klubmodul_runner
from .misc import GFXDisplay, Watchdog, queries
from .reader import opticon_reader
from .routers import admin, auth, card, me

log = logging.getLogger(__name__)
watchdog = Watchdog()

origins = [
    "https://lockoff.nkk.dk",
    "http://localhost:5173",
    "http://192.168.2.186:5173",
    "http://192.168.1.168:5173",
]


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


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(card.router)
app.include_router(me.router)
app.include_router(admin.router)


@app.get("/healtz", dependencies=[Depends(RateLimiter(times=2, seconds=5))])
async def healthz():
    if not watchdog.healthy():
        raise HTTPException(
            status_code=500, detail="watchdog report a task is not running"
        )
    return {"everything": "is awesome"}
