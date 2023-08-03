import pytest
from lockoff.access_token import TokenType, TokenError
from lockoff.reader import (
    O_CMD,
    check_dayticket,
    check_member,
    check_qrcode,
    o_cmd,
    opticon_reader,
)


@pytest.mark.asyncio
async def test_check_qr_code(testing_get_db):
    with pytest.raises(TokenError):
        await check_qrcode(qr_code="trash", conn=testing_get_db)


@pytest.mark.asyncio
async def test_member(testing_get_db):
    await check_member(user_id=0, member_type=TokenType.NORMAL, conn=testing_get_db)

    with pytest.raises(TokenError):
        await check_member(
            user_id=1000, member_type=TokenType.NORMAL, conn=testing_get_db
        )
