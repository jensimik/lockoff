import asyncio
import logging
from contextlib import asynccontextmanager

import redis.asyncio as redis
from fastapi import Depends, FastAPI, HTTPException
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter

from .config import settings
from .display import GFXDisplay
from .reader import opticon_reader
from .routers import auth, card
from .watchdog import Watchdog

log = logging.getLogger(__name__)
watchdog = Watchdog()


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.prod:
        # start watchdog
        asyncio.create_task(watchdog.runner())
        # start display
        display = GFXDisplay()
        await display.setup()
        display_task = asyncio.create_task(display.runner())
        watchdog.watch(display_task)
        # start opticon reader
        opticon_task = asyncio.create_task(opticon_reader(display=display))
        watchdog.watch(opticon_task)
        _redis = redis.from_url(
            settings.redis_url, encoding="utf-8", decode_responses=True
        )
        await FastAPILimiter.init(_redis)
    yield
    # clear things now at shutdown
    # nothing really have to be cleared


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)

app.include_router(auth.router)
app.include_router(card.router)


@app.get("/healtz", dependencies=[Depends(RateLimiter(times=2, seconds=5))])
async def healthz():
    if not watchdog.healthy():
        raise HTTPException(
            status_code=500, detail="watchdog report a process not running"
        )
    return {"everything": "is awesome"}
