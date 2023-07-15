import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .klubmodul import klubmodul_runner

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.prod:
        # start klubmodul syncer
        pass
        # klubmodul_task = asyncio.create_task(klubmodul_runner())
    yield
    # clear things now at shutdown
    # nothing really have to be cleared


app = FastAPI(
    title=settings.app_name,
    lifespan=lifespan,
)

# CORS
origins = [
    "https://lockoff.nkk.dk",
    "http://localhost:5137",
    "http://192.168.2.186:5137",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/healtz")
async def healthz():
    return {"everything": "is awesome"}


@app.post("/login")
async def login():
    pass


@app.post("/login_pin")
async def login_pin():
    pass


@app.post("/photo")
async def upload_profile_photo():
    pass


@app.get("/card.pdf")
async def card_pdf():
    pass


@app.get("/card.pkpass")
async def card_pkpass():
    pass
