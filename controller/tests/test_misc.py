import pytest
import asyncio
from lockoff.misc import GFXDisplay, simple_hash


@pytest.mark.asyncio
async def test_lcd(mock_serial):
    lcd = GFXDisplay()
    await lcd.setup(url=mock_serial.port)

    # test send message
    test_message = b"K"
    stub = mock_serial.stub(
        send_bytes=b"",
        receive_bytes=test_message.decode(),
    )
    await lcd.send_message(test_message)
    await asyncio.sleep(0.1)

    assert stub.called
    assert stub.calls == 1


def test_simple_hash():
    test_data1 = "testing1234"
    test_data2 = "1234testing"
    hash1 = simple_hash(test_data1)
    hash2 = simple_hash(test_data2)
    hash1_again = simple_hash(test_data1)
    assert hash1 != hash2
    assert hash1 == hash1_again
