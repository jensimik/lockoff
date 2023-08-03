import random
from contextlib import asynccontextmanager
from datetime import datetime, timedelta

import aiosqlite
import pyotp
import pytest
from fakeredis import aioredis
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi_limiter import FastAPILimiter
from lockoff.access_token import TokenType
from lockoff.config import settings
from lockoff.depends import get_db
from lockoff.misc import queries


@asynccontextmanager
async def testing_lifespan(app: FastAPI):
    _redis = aioredis.FakeRedis(encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(_redis)
    yield


async def testing_get_db():
    """Return a database connection for use as a dependency.
    This connection has the Row row factory automatically attached."""

    db = await aiosqlite.connect(":memory:")
    # Provide a smarter version of the results. This keeps from having to unpack
    # tuples manually.
    db.row_factory = aiosqlite.Row

    # setup schemas
    await queries.create_schema(db)

    # make some sample data in the database to run tests agains
    batch_id = datetime.utcnow().isoformat(timespec="seconds")
    for x in range(10):
        # insert test user
        await queries.upsert_user(
            db,
            user_id=x,
            name=f"test user {x}",
            member_type="FULL" if x in range(5) else "MORN",
            mobile=f"1000100{x}",
            email=f"test{x}@test.dk",
            batch_id=batch_id,
            totp_secret=pyotp.random_base32(),
            active=True if x < 8 else False,
        )
        # insert some daytickets
        await queries.insert_dayticket(db, batch_id=batch_id)
        # insert some log entry
        await queries.log_entry(
            db,
            user_id=random.randint(0, 9),
            token_type=random.choice(
                [TokenType.NORMAL, TokenType.MORNING, TokenType.DAY_TICKET]
            ).name,
            timestamp=int(
                (
                    datetime.utcnow() - timedelta(minutes=random.randint(0, 200))
                ).timestamp()
            ),
        )
    await db.commit()

    try:
        yield db
    finally:
        # test data is automatically cleared between tests
        await db.close()


@pytest.fixture
def client(mocker) -> TestClient:
    mocker.patch("lockoff.lifespan.lifespan", testing_lifespan)
    from lockoff.main import app

    app.dependency_overrides[get_db] = testing_get_db

    with TestClient(
        app=app,
        base_url="http://test",
    ) as client:
        yield client
