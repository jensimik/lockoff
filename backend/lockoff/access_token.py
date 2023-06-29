import calendar
import secrets
import struct
import hashlib
from datetime import datetime
from enum import Enum

import base45
from dateutil.relativedelta import relativedelta

from .db import DB_member

from .config import settings


class TokenType(Enum):
    NORMAL = 1
    MORNING = 2
    DAY_TICKET = 9


class TokenError(Exception):
    pass


def generate_access_token(
    user_id: int,
    token_type: TokenType = TokenType.NORMAL,
    expire_delta: relativedelta = relativedelta(
        day=20, month=1, years=1, hour=12, minute=0, second=0, microsecond=0
    ),
) -> bytes:
    """Generate a new access token
    the access token should be used as data in a QR code
    the QR code can be printed or used in apple/google wallet as a memebership card
    user_id 0 is a special case for day tickets

    Returns
    -------
    bytes
        the base45 encoded token

    """

    data = struct.pack(
        f">IIH",
        user_id,
        calendar.timegm((datetime.utcnow() + expire_delta).utctimetuple()),
        token_type.value,
    )

    nonce = secrets.token_bytes(settings.nonce_size)

    signature = hashlib.shake_256(data + nonce + settings.secret).digest(
        settings.digest_size
    )

    return base45.b45encode(data + nonce + signature)


def generate_dayticket_access_token() -> bytes:
    """generate a new access token only valid today as a dayticket"""
    return generate_access_token(
        user_id=0,
        token_type=TokenType.DAY_TICKET,
        expire_delta=relativedelta(hour=23, minute=59, second=0, microsecond=0),
    )


async def verify_access_token(token: str) -> bool:
    """verify the access token if possible to parse, 'signed' correct and is not expired

    Raises
    ------
    TokenError
        if not able to parse, signature wrong or expired

    Returns
    -------
    int
        user_id of the valid token

    """
    try:
        raw_token = base45.b45decode(token)
    except Exception as ex:
        raise TokenError(f"could not base45 decode token data: {ex}")

    try:
        user_id, expires, type_, _, signature = struct.unpack(
            f">IIH{settings.nonce_size}s{settings.digest_size}s", raw_token
        )
        data = raw_token[: -settings.digest_size]
        token_type = TokenType(type_)
        expires_datetime = datetime.utcfromtimestamp(expires)
    except Exception as ex:
        raise TokenError(f"could not unpack data: {ex}")

    if not secrets.compare_digest(
        hashlib.shake_256(data + settings.secret).digest(settings.digest_size),
        signature,
    ):
        raise TokenError("could not verify signature")

    if datetime.utcnow() > expires_datetime:
        raise TokenError("token is expired")

    # check in database
    if token_type in [TokenType.NORMAL, TokenType.MORNING]:
        async with DB_member as db:
            d = db.get(doc_id=user_id)
            if not d:
                raise TokenError("did you cancel your membership?")
    elif token_type == TokenType.DAY_TICKET:
        # TODO: could save in db-cache the id of the day-ticket and peg it to today
        pass

    return True
