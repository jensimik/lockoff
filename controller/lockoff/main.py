import logging

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi_limiter.depends import RateLimiter

from .config import settings
from .misc import lifespan, watchdog
from .routers import admin, auth, card, me

log = logging.getLogger(__name__)

origins = [
    "https://lockoff.nkk.dk",
    "http://localhost:5173",
    "http://192.168.2.186:5173",
    "http://192.168.1.168:5173",
]


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
