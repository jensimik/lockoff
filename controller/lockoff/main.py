import asyncio
import logging
import secrets
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from .config import settings
from .klubmodul import Klubmodul
from .reader import opticon_reader
from .display import GFXDisplay
from .watchdog import Watchdog

log = logging.getLogger(__name__)
security = HTTPBasic()
watchdog = Watchdog()


# http basic auth as simple auth for api endpoints
def get_current_username(
    credentials: Annotated[HTTPBasicCredentials, Depends(security)]
):
    current_username_bytes = credentials.username.encode("utf8")
    is_correct_username = secrets.compare_digest(
        current_username_bytes, settings.basic_auth_username
    )
    current_password_bytes = credentials.password.encode("utf8")
    is_correct_password = secrets.compare_digest(
        current_password_bytes, settings.basic_auth_password
    )
    if not (is_correct_username and is_correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


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
        # start klubmodul syncer
        km = Klubmodul()
        klubmodul_task = asyncio.create_task(km.runner())
        watchdog.watch(klubmodul_task)
    yield
    # clear things now at shutdown
    # nothing really have to be cleared


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)


@app.get("/healtz")
async def healthz():
    if not watchdog.healthy():
        raise HTTPException(
            status_code=500, detail="watchdog report a process not running"
        )
    return {"everything": "is awesome"}


@app.get("/dayticket")
async def get_dayticket_sheets(username: Annotated[str, Depends(get_current_username)]):
    pass
