import pytest
import asyncio
from datetime import datetime
from lockoff.config import settings
from lockoff.misc import GFXDisplay, buzz_in


@pytest.mark.asyncio
async def test_display(mock_serial):
    lcd = GFXDisplay()
    await lcd.setup(url=mock_serial.port)

    # test send message
    test_message = b"K"
    stub = mock_serial.stub(
        send_bytes=b"",
        receive_bytes=test_message,
    )
    await lcd.send_message(test_message)
    await asyncio.sleep(0.1)

    assert stub.called
    assert stub.calls == 1

    now = datetime.now(tz=settings.tz)
    stub = mock_serial.stub(
        send_bytes=b"",
        receive_bytes=b"," if now.hour < 7 else b".",
    )
    await lcd.runner(one_time_run=True)

    await asyncio.sleep(0.1)
    assert stub.called
    assert stub.calls == 1


@pytest.mark.asyncio
async def test_buzz_in(mocker):
    relay = mocker.patch("lockoff.misc.relay")
    await buzz_in(sleep=0)
    relay.on.assert_called_once()
    relay.off.assert_called_once()
