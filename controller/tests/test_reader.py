import pytest
from lockoff.access_token import generate_access_token, TokenType, TokenError
from lockoff.reader import (
    O_CMD,
    check_dayticket,
    check_member,
    check_qrcode,
    o_cmd,
    opticon_reader,
    buzz_in,
)
from lockoff.misc import GFXDisplay


@pytest.mark.asyncio
async def test_check_qr_code(conn):
    with pytest.raises(TokenError):
        await check_qrcode(qr_code="trash", conn=conn)


@pytest.mark.asyncio
async def test_member(conn):
    await check_member(user_id=0, member_type=TokenType.NORMAL, conn=conn)

    with pytest.raises(TokenError):
        await check_member(user_id=1000, member_type=TokenType.NORMAL, conn=conn)


@pytest.mark.asyncio
async def test_dayticket(conn):
    await check_dayticket(user_id=0, conn=conn)


@pytest.mark.asyncio
async def test_reader_ok_token(mocker, conn, mock_serial):
    gfxdisplay = mocker.async_stub(name="display")
    buzz_in = mocker.patch("lockoff.reader.buzz_in")
    # inject test db
    mocker.patch("aiosqlite.connect", lambda _: conn)

    ok_token = generate_access_token(user_id=1, token_type=TokenType.NORMAL)

    mock_serial.stub(
        send_bytes=ok_token + b"\r",
        receive_bytes=O_CMD.OK_SOUND + O_CMD.OK_LED,
    )
    await opticon_reader(display=gfxdisplay, run_infinite=False, url=mock_serial.port)

    gfxdisplay.send_message.assert_awaited_once_with(b"K")
    buzz_in.assert_awaited_once()


@pytest.mark.asyncio
async def test_reader_bad_token(mocker, conn, mock_serial):
    gfxdisplay = mocker.async_stub(name="display")
    buzz_in = mocker.patch("lockoff.reader.buzz_in")
    mocker.patch("aiosqlite.connect", lambda _: conn)

    ok_token = generate_access_token(user_id=1, token_type=TokenType.NORMAL)
    bad_token = bytearray(ok_token)
    bad_token[-1] = bad_token[-1] + 1
    bad_token = bytes(bad_token)

    mock_serial.stub(
        send_bytes=bad_token + b"\r",
        receive_bytes=O_CMD.ERROR_SOUND + O_CMD.ERROR_LED,
    )
    await opticon_reader(display=gfxdisplay, run_infinite=False, url=mock_serial.port)

    gfxdisplay.send_message.assert_awaited_once_with(b"S")
    buzz_in.assert_not_awaited()
