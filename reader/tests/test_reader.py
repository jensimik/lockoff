import asyncio

import pytest
from lockoff.misc import O_CMD, GFXDisplay
from lockoff.reader import (
    Reader,
)
from lockoff.config import settings


@pytest.mark.asyncio
async def test_reader_ok(mocker, mock_serial, httpx_mock):
    httpx_mock.add_response(
        method="POST", url=settings.backend_url, json={"status": "OK"}
    )
    buzz_in = mocker.patch("lockoff.reader.buzz_in")
    send_message = mocker.patch("lockoff.misc.GFXDisplay.send_message")
    display = GFXDisplay()

    ok_token = b"test1234"

    async def fake_readuntil(*args, **kwargs):
        return ok_token + b"\r"

    mocker.patch("asyncio.StreamReader.readuntil", fake_readuntil)
    stream_writer = mocker.patch("asyncio.StreamWriter.write")

    reader = Reader()
    await reader.setup(display=display, url=mock_serial.port)

    await reader.runner(one_time_run=True)

    # sleep a little to allow background tasks to callback
    await asyncio.sleep(0.1)

    stream_writer.assert_any_call(O_CMD.OK_SOUND)
    stream_writer.assert_any_call(O_CMD.OK_LED)

    send_message.assert_awaited_once_with(b"K")
    buzz_in.assert_awaited_once()


@pytest.mark.asyncio
async def test_reader_fail(mocker, mock_serial, httpx_mock):
    httpx_mock.add_response(
        method="POST",
        url=settings.backend_url,
        json={"detail": {"code": "Q", "reason": "failed to do something"}},
        status_code=418,
    )
    buzz_in = mocker.patch("lockoff.reader.buzz_in")
    send_message = mocker.patch("lockoff.misc.GFXDisplay.send_message")
    display = GFXDisplay()

    ok_token = b"test1234"

    async def fake_readuntil(*args, **kwargs):
        return ok_token + b"\r"

    mocker.patch("asyncio.StreamReader.readuntil", fake_readuntil)
    stream_writer = mocker.patch("asyncio.StreamWriter.write")

    reader = Reader()
    await reader.setup(display=display, url=mock_serial.port)

    await reader.runner(one_time_run=True)

    # sleep a little to allow background tasks to callback
    await asyncio.sleep(0.1)

    stream_writer.assert_any_call(O_CMD.ERROR_LED)
    stream_writer.assert_any_call(O_CMD.ERROR_LED)

    send_message.assert_awaited_once_with(b"Q")
    buzz_in.assert_not_awaited()
