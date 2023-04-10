import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

from . import db, schemas
from .barcode import barcode_reader
from .config import settings
from .display import LCD
from .klubmodul import Klubmodul
from .watchdog import Watchdog

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    await db.database.connect()
    if settings.prod:
        # start LCD runner
        lcd = LCD()
        await lcd.setup()
        lcd_task = asyncio.create_task(lcd.runner())
        # start barcode reader
        barcode_task = asyncio.create_task(barcode_reader(lcd=lcd))
        # start klubmodul syncer
        km = Klubmodul(
            username=settings.klubmodul_username, password=settings.klubmodul_password
        )
        klubmodul_task = asyncio.create_task(km.runner())
        # start watchdog
        wd = Watchdog(watch=[lcd_task, barcode_task, klubmodul_task])
        asyncio.create_task(wd.runner())
    yield
    # clear things now at shutdown
    if settings.prod:
        barcode_task.cancel()
        try:
            await barcode_task
        except asyncio.CancelledError:
            log.info("barcode_reader is canceled now")
        lcd_task.cancel()
        try:
            await lcd_task
        except asyncio.CancelledError:
            log.info("lcd is canceled now")
    await db.database.disconnect()


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)


@app.get("/healtz")
async def healthz():
    return {"everything": "is awesome"}


@app.get("/tokens")  # , response_model=list[schemas.Token])
async def get_tokens():
    query = db.tokens.select()
    return await db.database.fetch_all(query)
