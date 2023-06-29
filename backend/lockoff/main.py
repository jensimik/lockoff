import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from . import db
from .reader import opticon_reader
from .config import settings
from .klubmodul import Klubmodul
from .watchdog import Watchdog

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.prod:
        # start barcode reader
        opticon_task = asyncio.create_task(opticon_reader())
        # start klubmodul syncer
        km = Klubmodul()
        klubmodul_task = asyncio.create_task(km.runner())
        # start watchdog
        wd = Watchdog(watch=[opticon_task, klubmodul_task])
        asyncio.create_task(wd.runner())
    yield
    # clear things now at shutdown
    if settings.prod:
        opticon_task.cancel()
        try:
            await opticon_task
        except asyncio.CancelledError:
            log.info("opticon_reader is canceled now")


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)


@app.get("/healtz")
async def healthz():
    return {"everything": "is awesome"}
