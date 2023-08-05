import asyncio
from contextlib import asynccontextmanager

import pytest
from fakeredis import aioredis


@pytest.mark.asyncio
async def test_lifespan(mocker, conn):
    mocker.patch("lockoff.lifespan.redis", aioredis.FakeRedis)

    display_setup = mocker.patch("lockoff.lifespan.GFXDisplay.setup")
    display_runner = mocker.patch("lockoff.lifespan.GFXDisplay.runner")
    reader_setup = mocker.patch("lockoff.lifespan.Reader.setup")
    reader_runner = mocker.patch("lockoff.lifespan.Reader.runner")

    # inject test db
    @asynccontextmanager
    async def get_conn(*args, **kwargs):
        yield conn

    mocker.patch("aiosqlite.connect", get_conn)

    from lockoff.lifespan import lifespan
    from lockoff.main import app

    async with lifespan(app=app) as _:
        display_setup.assert_awaited_once()
        display_runner.assert_called_once()
        reader_setup.assert_awaited_once()
        reader_runner.assert_called_once()
