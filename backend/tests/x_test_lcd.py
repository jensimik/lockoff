import pytest
import asyncio
from lockoff.display import LCD


@pytest.mark.asyncio
async def test_lcd(mock_serial):
    lcd = LCD()
    stub = mock_serial.stub(
        send_bytes=b"",
        receive_bytes=b"\xfe\x58",
    )
    await lcd.setup(url=mock_serial.port)

    # test clear screen
    await lcd.clear_screen()
    await asyncio.sleep(0.1)

    assert stub.called
    assert stub.calls == 1

    # test line1 message
    test_message = "test message"
    stub = mock_serial.stub(
        send_bytes=b"",
        receive_bytes=test_message.encode(),
    )
    lcd.line1_message(test_message)
    await lcd.drain()
    await asyncio.sleep(0.1)

    assert stub.called
    assert stub.calls == 1

    # test line2 message
    test_message = "test message2"
    stub = mock_serial.stub(
        send_bytes=b"",
        receive_bytes=bytes([0xFE, 0x47, 1, 2]) + test_message.encode(),
    )
    lcd.line2_message(test_message)
    await lcd.drain()
    await asyncio.sleep(0.1)

    assert stub.called
    assert stub.calls == 1
