import random
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

import pyotp
import pytest
import pytest_asyncio
from fakeredis import aioredis
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi_limiter import FastAPILimiter
from lockoff.access_token import TokenMedia, TokenType
from lockoff.config import settings
from lockoff.db import DB, AccessLog, Dayticket, GPass, User, APDevice, APPass, APReg
from lockoff.misc import simple_hash
from piccolo.table import create_db_tables

TOTP_SECRET = "H6IC425Q5IFZYAP4VINKRVHX7ZIEKO7E"


@asynccontextmanager
async def testing_lifespan(app: FastAPI):
    _redis = aioredis.FakeRedis(encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(_redis)
    yield


@pytest_asyncio.fixture(autouse=True)
async def sample_data():
    # create tables
    async with DB.transaction():
        await create_db_tables(
            User,
            Dayticket,
            AccessLog,
            APReg,
            APDevice,
            APPass,
            GPass,
            if_not_exists=True,
        )
    # make some sample data in the database to run tests agains
    batch_id = datetime.now(tz=settings.tz).isoformat(timespec="seconds")
    async with DB.transaction():
        for x in range(10):
            # insert test user
            try:
                await User.insert(
                    User(
                        id=x,
                        name=f"test user {x}",
                        token_type=TokenType.NORMAL
                        if x in range(5)
                        else TokenType.MORNING,
                        mobile=simple_hash(f"1000100{x}"),
                        email=simple_hash(f"test{x}@test.dk"),
                        batch_id=batch_id,
                        totp_secret=TOTP_SECRET,
                        active=True if x < 8 else False,
                    )
                ).on_conflict(
                    target=User.id,
                    action="DO UPDATE",
                    values=[
                        User.name,
                        User.token_type,
                        User.mobile,
                        User.email,
                        User.batch_id,
                        User.totp_secret,
                        User.active,
                    ],
                )
            except Exception as ex:
                print(f"failed user inser with {ex}")
            try:
                await AccessLog.insert(
                    AccessLog(
                        id=None,
                        obj_id=x,
                        token_type=random.choice(
                            [TokenType.NORMAL, TokenType.MORNING, TokenType.DAY_TICKET]
                        ),
                        token_media=random.choice(
                            [TokenMedia.DIGITAL, TokenMedia.PRINT]
                        ),
                        timestamp=(
                            (
                                datetime.now(tz=settings.tz)
                                - timedelta(minutes=random.randint(0, 200))
                            ).isoformat(timespec="seconds")
                        ),
                    )
                )
            except Exception as ex:
                print(f"failed create access log with {ex}")
            try:
                await Dayticket.insert(
                    Dayticket(
                        id=x,
                        expires=0,
                    )
                ).on_conflict(
                    action="DO UPDATE",
                    values=[Dayticket.expires],
                )
            except Exception as ex:
                print(f"failed create dayticket with {ex}")
        expired = datetime.now(tz=settings.tz) - timedelta(hours=1)
        valid = datetime.now(tz=settings.tz) + timedelta(hours=1)
        await Dayticket.update({Dayticket.expires: int(expired.timestamp())}).where(
            Dayticket.id == 2
        )
        await Dayticket.update({Dayticket.expires: int(valid.timestamp())}).where(
            Dayticket.id == 3
        )
        await User.update({User.season_digital: str(settings.current_season)}).where(
            User.id == 7
        )


@pytest.fixture
def client(mocker) -> TestClient:
    """unauthenticated client"""
    mocker.patch("lockoff.lifespan.lifespan", testing_lifespan)
    from lockoff.main import app

    with TestClient(
        app=app,
        base_url="http://test",
    ) as client:
        yield client


@pytest.fixture
def a0client(mocker) -> TestClient:
    """authenticated client without admin scope"""
    mocker.patch("lockoff.lifespan.lifespan", testing_lifespan)
    from lockoff.main import app

    with TestClient(
        app=app,
        base_url="http://test",
    ) as client:
        totp = pyotp.TOTP(TOTP_SECRET)
        data = {"username": "10001000", "username_type": "mobile", "totp": totp.now()}
        response = client.post("/login", json=data)
        json = response.json()

        client.headers = {
            "Authorization": f"{json['token_type']} {json['access_token']}"
        }

        yield client


@pytest.fixture
def a1client(mocker) -> TestClient:
    """authenticated client with admin scope"""
    mocker.patch("lockoff.lifespan.lifespan", testing_lifespan)
    from lockoff.main import app

    with TestClient(
        app=app,
        base_url="http://test",
    ) as client:
        totp = pyotp.TOTP(TOTP_SECRET)
        data = {"username": "10001001", "username_type": "mobile", "totp": totp.now()}
        response = client.post("/login", json=data)
        json = response.json()

        client.headers = {
            "Authorization": f"{json['token_type']} {json['access_token']}"
        }

        yield client
