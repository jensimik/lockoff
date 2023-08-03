from contextlib import asynccontextmanager

import aiosqlite
import pytest
from fakeredis import aioredis
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi_limiter import FastAPILimiter
from lockoff.config import settings
from lockoff.misc import queries
from lockoff.depends import get_db
import aiosql


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

    try:
        yield db
    finally:
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
