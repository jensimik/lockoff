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
async def test_reader(mocker, conn, mock_serial):
    gfxdisplay = mocker.patch("lockoff.misc.GFXDisplay")
    display = mocker.async_stub(name="display")
    buzz_in = mocker.patch("lockoff.reader.buzz_in")
    mocker.patch("aiosqlite.connect", lambda _: conn)

    ok_token = generate_access_token(user_id=1, token_type=TokenType.NORMAL)

    stub = mock_serial.stub(
        send_bytes=ok_token + b"\r",
        receive_bytes=O_CMD.OK_SOUND + O_CMD.OK_LED,
    )
    await opticon_reader(display=gfxdisplay, run_infinite=False, url=mock_serial.port)

    assert gfxdisplay.send_message.called_once_with(b"K")
    assert buzz_in.called_once()