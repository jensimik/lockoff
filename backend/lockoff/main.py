import logging

import sentry_sdk
from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter.depends import RateLimiter

from .config import settings
from .lifespan import lifespan, watchdog
from .routers import (
    admin,
    apple_wallet,
    auth,
    card,
    google_wallet,
    me,
    reader,
    public_stats,
)

log = logging.getLogger(__name__)

origins = [
    "https://lockoff.nkk.dk",
    "https://nkk.klub-modul.dk",
    "http://localhost:5173",
    "http://192.168.2.186:5173",
    "http://192.168.1.168:5173",
]

if settings.sentry_dsn:
    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        traces_sample_rate=0.5,
    )

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
app.include_router(reader.router)
app.include_router(public_stats.router)
app.include_router(admin.router, prefix="/admin")
app.include_router(apple_wallet.router, prefix="/apple-wallet")
app.include_router(google_wallet.router, prefix="/google-wallet")


@app.api_route("/healtz", methods=["GET", "HEAD"])
# @app.get("/healtz")  # , dependencies=[Depends(RateLimiter(times=2, seconds=5))])
async def healthz():
    if not watchdog.healthy():
        raise HTTPException(
            status_code=500, detail="watchdog report a task is not running"
        )
    return {"everything": "is awesome"}
