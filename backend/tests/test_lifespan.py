import pytest
from fakeredis import aioredis


@pytest.mark.asyncio
async def test_lifespan(mocker):
    mocker.patch("lockoff.lifespan.redis", aioredis.FakeRedis)
    google_wallet = mocker.patch("lockoff.lifespan.GooglePass")

    from lockoff.lifespan import lifespan
    from lockoff.main import app

    async with lifespan(app=app) as _:
        assert True
        # display_setup.assert_awaited_once()
        # display_runner.assert_called_once()
        # reader_setup.assert_awaited_once()
        # reader_runner.assert_called_once()
