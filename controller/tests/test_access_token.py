import pytest
from dateutil.relativedelta import relativedelta
from fastapi import HTTPException
from lockoff.access_token import (
    TokenError,
    TokenType,
    generate_access_token,
    generate_dl_token,
    verify_access_token,
    verify_dl_token,
)


@pytest.mark.parametrize(
    "user_id",
    (0, 1, 2, 3),
)
def test_dl_token(user_id):
    token = generate_dl_token(user_id=user_id)
    assert verify_dl_token(token) == user_id

    token_expired = generate_dl_token(user_id, expire_delta=relativedelta(hours=-10))
    with pytest.raises(HTTPException):
        verify_dl_token(token_expired)

    # modify signature
    token = token[:-1] + "A"
    with pytest.raises(HTTPException):
        verify_dl_token(token)


@pytest.mark.parametrize(
    ["user_id", "token_type"],
    (
        (0, TokenType.NORMAL),
        (1, TokenType.MORNING),
        (2, TokenType.DAY_TICKET),
        (3, TokenType.NORMAL),
    ),
)
def test_token(user_id, token_type):
    # ok
    token_bytes = generate_access_token(user_id=user_id, token_type=token_type)
    token_str = token_bytes.decode()

    verify_user_id, verify_token_type = verify_access_token(token_str)
    assert user_id == verify_user_id
    assert token_type == verify_token_type

    # try to change a bit in signature part
    ba = bytearray(token_bytes)
    ba[-1] = ba[-1] + 1
    ba = bytes(ba)
    token_str_bad_signature = ba.decode()
    with pytest.raises(TokenError):
        verify_access_token(token_str_bad_signature)

    # expired
    token_bytes_expired = generate_access_token(
        user_id=user_id, token_type=token_type, expire_delta=relativedelta(hours=-10)
    )
    token_str_expired = token_bytes_expired.decode()
    with pytest.raises(TokenError):
        verify_access_token(token_str_expired)

    # gibberish
    with pytest.raises(TokenError):
        verify_access_token("gibberish")
