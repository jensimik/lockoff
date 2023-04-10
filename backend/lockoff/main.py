import asyncio
import logging
from contextlib import asynccontextmanager

import db
import schemas
from fastapi import FastAPI

from .barcode import barcode_reader
from .config import settings
from .klubmodul import Klubmodul
from .repeat_every_helper import repeat_every

log = logging.getLogger(__name__)
km = Klubmodul(
    username=settings.klubmodul_username, password=settings.klubmodul_password
)


# refresh klubmodul every 12 hours
@repeat_every(seconds=60 * 60 * 12)
async def _refresh_klubmodul():
    await km.refresh()


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.database.connect()
    await _refresh_klubmodul()
    barcode_task = asyncio.create_task(barcode_reader())
    yield
    # clear things now at shutdown
    barcode_task.cancel()
    try:
        await barcode_task
    except asyncio.CancelledError:
        log.info("barcode_reader is canceled now")
    await db.database.disconnect()


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)


@app.get("/healtz")
async def healthz():
    return {"everything": "is awesome"}


@app.get("/tokens", response_model=[schemas.Token])
async def get_tokens():
    query = db.tokens.select()
    return await db.database.fetch_all(query)


# TODO: use hardware watchdog
