from contextlib import asynccontextmanager

import aiosqlite
import pytest
from fakeredis import aioredis
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi_limiter import FastAPILimiter
from lockoff.config import settings
from lockoff.misc import queries


@asynccontextmanager
async def testing_lifespan(app: FastAPI):
    _redis = aioredis.FakeRedis(encoding="utf-8", decode_responses=True)
    await FastAPILimiter.init(_redis)
    async with aiosqlite.connect(settings.db_file) as conn:
        await queries.create_schema(conn)
        await conn.commit()
    yield


@pytest.fixture
def client(mocker) -> TestClient:
    mocker.patch("lockoff.lifespan.lifespan", testing_lifespan)
    from lockoff.main import app

    with TestClient(
        app=app,
        base_url="http://test",
    ) as client:
        yield client
