import pytest
from dateutil.relativedelta import relativedelta
from fastapi import HTTPException
from lockoff.access_token import (
    TokenError,
    TokenType,
    TokenMedia,
    generate_access_token,
    generate_dl_admin_token,
    generate_dl_member_token,
    verify_access_token,
    verify_dl_admin_token,
    verify_dl_member_token,
)


@pytest.mark.parametrize(
    ["user_id", "gen_func", "ver_func"],
    (
        (0, generate_dl_member_token, verify_dl_member_token),
        (1, generate_dl_member_token, verify_dl_member_token),
        (2, generate_dl_member_token, verify_dl_member_token),
        (3, generate_dl_member_token, verify_dl_member_token),
        (0, generate_dl_admin_token, verify_dl_admin_token),
        (1, generate_dl_admin_token, verify_dl_admin_token),
        (2, generate_dl_admin_token, verify_dl_admin_token),
        (3, generate_dl_admin_token, verify_dl_admin_token),
    ),
)
def test_dl_token(user_id, gen_func, ver_func):
    token = gen_func(user_id=user_id)
    assert ver_func(token) == user_id

    token_expired = gen_func(user_id, expire_delta=relativedelta(hours=-10))
    with pytest.raises(HTTPException):
        ver_func(token_expired)

    # modify signature
    modify = "A" if token[-1] != "A" else "B"
    token = token[:-1] + modify
    with pytest.raises(HTTPException):
        ver_func(token)


@pytest.mark.parametrize(
    ["user_id", "token_type", "token_media"],
    (
        (0, TokenType.NORMAL, TokenMedia.DIGITAL),
        (1, TokenType.MORNING, TokenMedia.DIGITAL),
        (2, TokenType.DAY_TICKET, TokenMedia.DIGITAL),
        (3, TokenType.NORMAL, TokenMedia.DIGITAL),
        (0, TokenType.NORMAL, TokenMedia.PRINT),
        (1, TokenType.MORNING, TokenMedia.PRINT),
        (2, TokenType.DAY_TICKET, TokenMedia.PRINT),
        (3, TokenType.NORMAL, TokenMedia.PRINT),
    ),
)
def test_token(user_id, token_type, token_media):
    # ok
    token_bytes = generate_access_token(
        user_id=user_id, token_type=token_type, token_media=token_media
    )
    token_str = token_bytes.decode()

    verify_user_id, verify_token_type, verify_token_media = verify_access_token(
        token_str
    )
    assert user_id == verify_user_id
    assert token_type == verify_token_type
    assert token_media == verify_token_media

    # try to change a bit in signature part
    ba = bytearray(token_bytes)
    ba[-1] = ba[-1] + 1
    ba = bytes(ba)
    token_str_bad_signature = ba.decode()
    with pytest.raises(TokenError):
        verify_access_token(token_str_bad_signature)

    # expired
    token_bytes_expired = generate_access_token(
        user_id=user_id,
        token_type=token_type,
        token_media=token_media,
        expire_delta=relativedelta(hours=-10),
    )
    token_str_expired = token_bytes_expired.decode()
    with pytest.raises(TokenError):
        verify_access_token(token_str_expired)

    # gibberish
    with pytest.raises(TokenError):
        verify_access_token("gibberish")

    # giberish base45 encoded
    with pytest.raises(TokenError):
        verify_access_token("D3DVJC5$C+EDE2")
