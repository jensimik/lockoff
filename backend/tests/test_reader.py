import asyncio

import pytest
from lockoff.access_token import TokenError, TokenType, generate_access_token

# from lockoff.misc import O_CMD, GFXDisplay
from lockoff.routers.reader import (
    # Reader,
    check_dayticket,
    check_member,
    check_qrcode,
    check_totp,
)


@pytest.mark.parametrize(
    ["qr_code", "_raise"],
    (
        ("trash", TokenError),
        (generate_access_token(user_id=1, token_type=TokenType.NORMAL), False),
        (generate_access_token(user_id=1, token_type=TokenType.MORNING), False),
        (generate_access_token(user_id=1, token_type=TokenType.DAY_TICKET), False),
        (generate_access_token(user_id=2, token_type=TokenType.DAY_TICKET), TokenError),
        (generate_access_token(user_id=3, token_type=TokenType.DAY_TICKET), False),
    ),
)
@pytest.mark.asyncio
async def test_check_qr_code(qr_code, _raise):
    if _raise:
        with pytest.raises(_raise):
            await check_qrcode(qr_code=qr_code)
    else:
        await check_qrcode(qr_code=qr_code)


@pytest.mark.asyncio
async def test_check_totp():
    with pytest.raises(TokenError):
        await check_totp(user_id=1, totp="12345678")


@pytest.mark.asyncio
async def test_member():
    await check_member(user_id=0, member_type=TokenType.NORMAL)

    with pytest.raises(TokenError):
        await check_member(user_id=1000, member_type=TokenType.NORMAL)


@pytest.mark.asyncio
async def test_dayticket():
    await check_dayticket(user_id=0)


@pytest.mark.asyncio
async def na_test_reader_ok_token(mocker, mock_serial):
    send_message = mocker.patch("lockoff.misc.GFXDisplay.send_message")
    buzz_in = mocker.patch("lockoff.reader.buzz_in")
    ok_token = generate_access_token(user_id=1, token_type=TokenType.NORMAL)

    async def fake_readuntil(*args, **kwargs):
        return ok_token + b"\r"

    mocker.patch("asyncio.StreamReader.readuntil", fake_readuntil)
    stream_writer = mocker.patch("asyncio.StreamWriter.write")
    display = GFXDisplay()

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
async def na_test_reader_bad_token(mocker, mock_serial):
    send_message = mocker.patch("lockoff.misc.GFXDisplay.send_message")
    buzz_in = mocker.patch("lockoff.reader.buzz_in")
    ok_token = generate_access_token(user_id=1, token_type=TokenType.NORMAL)
    bad_token = bytearray(ok_token)
    bad_token[-1] = bad_token[-4]
    bad_token[-2] = bad_token[-5]
    bad_token[-3] = bad_token[-6]
    bad_token = bytes(bad_token)

    async def fake_readuntil(*args, **kwargs):
        return bad_token + b"\r"

    mocker.patch("asyncio.StreamReader.readuntil", fake_readuntil)
    stream_writer = mocker.patch("asyncio.StreamWriter.write")
    display = GFXDisplay()

    reader = Reader()
    await reader.setup(display=display, url=mock_serial.port)

    await reader.runner(one_time_run=True)

    # sleep a little to allow background tasks to callback
    await asyncio.sleep(0.1)

    stream_writer.assert_any_call(O_CMD.ERROR_SOUND)
    stream_writer.assert_any_call(O_CMD.ERROR_LED)

    send_message.assert_awaited_once_with(b"S")
    buzz_in.assert_not_awaited()
