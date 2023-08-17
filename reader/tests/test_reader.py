import asyncio

import pytest
from lockoff.misc import O_CMD, GFXDisplay
from lockoff.reader import (
    Reader,
)


# @pytest.mark.asyncio
# async def na_test_reader_ok_token(mocker, mock_serial):
#     send_message = mocker.patch("lockoff.misc.GFXDisplay.send_message")
#     buzz_in = mocker.patch("lockoff.reader.buzz_in")
#     ok_token = generate_access_token(user_id=1, token_type=TokenType.NORMAL)

#     async def fake_readuntil(*args, **kwargs):
#         return ok_token + b"\r"

#     mocker.patch("asyncio.StreamReader.readuntil", fake_readuntil)
#     stream_writer = mocker.patch("asyncio.StreamWriter.write")
#     display = GFXDisplay()

#     reader = Reader()
#     await reader.setup(display=display, url=mock_serial.port)

#     await reader.runner(one_time_run=True)

#     # sleep a little to allow background tasks to callback
#     await asyncio.sleep(0.1)

#     stream_writer.assert_any_call(O_CMD.OK_SOUND)
#     stream_writer.assert_any_call(O_CMD.OK_LED)

#     send_message.assert_awaited_once_with(b"K")
#     buzz_in.assert_awaited_once()


# @pytest.mark.asyncio
# async def na_test_reader_bad_token(mocker, mock_serial):
#     send_message = mocker.patch("lockoff.misc.GFXDisplay.send_message")
#     buzz_in = mocker.patch("lockoff.reader.buzz_in")
#     ok_token = generate_access_token(user_id=1, token_type=TokenType.NORMAL)
#     bad_token = bytearray(ok_token)
#     bad_token[-1] = bad_token[-4]
#     bad_token[-2] = bad_token[-5]
#     bad_token[-3] = bad_token[-6]
#     bad_token = bytes(bad_token)

#     async def fake_readuntil(*args, **kwargs):
#         return bad_token + b"\r"

#     mocker.patch("asyncio.StreamReader.readuntil", fake_readuntil)
#     stream_writer = mocker.patch("asyncio.StreamWriter.write")
#     display = GFXDisplay()

#     reader = Reader()
#     await reader.setup(display=display, url=mock_serial.port)

#     await reader.runner(one_time_run=True)

#     # sleep a little to allow background tasks to callback
#     await asyncio.sleep(0.1)

#     stream_writer.assert_any_call(O_CMD.ERROR_SOUND)
#     stream_writer.assert_any_call(O_CMD.ERROR_LED)

#     send_message.assert_awaited_once_with(b"S")
#     buzz_in.assert_not_awaited()
