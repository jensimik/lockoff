import pytest


@pytest.mark.asyncio
async def test_lifespan(mocker):
    display_setup = mocker.patch("lockoff.lifespan.GFXDisplay.setup")
    display_runner = mocker.patch("lockoff.lifespan.GFXDisplay.runner")
    reader_setup = mocker.patch("lockoff.lifespan.Reader.setup")
    reader_runner = mocker.patch("lockoff.lifespan.Reader.runner")

    from lockoff.lifespan import lifespan
    from lockoff.main import app

    async with lifespan(app=app) as _:
        display_setup.assert_awaited_once()
        display_runner.assert_called_once()
        reader_setup.assert_awaited_once()
        reader_runner.assert_called_once()
