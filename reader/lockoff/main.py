import logging

import sentry_sdk
from fastapi import FastAPI, HTTPException

from .config import settings
from .lifespan import lifespan, watchdog

log = logging.getLogger(__name__)

if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        traces_sample_rate=0.5,
    )

app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)


@app.get("/healtz")
async def healthz():
    if not watchdog.healthy():
        raise HTTPException(
            status_code=500, detail="watchdog report a task is not running"
        )
    return {"everything": "is awesome"}
