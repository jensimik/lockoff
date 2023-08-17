import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI

from .misc import GFXDisplay, watchdog
from .reader import Reader


@asynccontextmanager
async def lifespan(app: FastAPI):
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
    yield
    # clear things now at shutdown
    # nothing really have to be cleared
