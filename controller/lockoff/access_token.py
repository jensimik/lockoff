import calendar
import hashlib
import secrets
import struct
import logging
from datetime import datetime
from enum import Enum

import base45
from dateutil.relativedelta import relativedelta
from tinydb.table import Document

from .config import settings
from .db import DB_dayticket, DB_member

log = logging.getLogger(__name__)
door_log = logging.getLogger("door")


class TokenType(Enum):
    NORMAL = 1
    MORNING = 2
    DAY_TICKET = 3
    DAY_TICKET_HACK = 4


class TokenError(Exception):
    def __init__(self, message, code=b"Q"):
        super().__init__(message)
        self.code = code


def log_and_raise_token_error(message, code=b"Q", level=logging.WARN):
    log.log(level=level, msg=message)
    raise TokenError(message, code=code)


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

    expire = datetime.now(tz=settings.tz) + expire_delta
    data = struct.pack(
        f">IIH",
        user_id,
        calendar.timegm(expire.utctimetuple()),
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


def verify_access_token(token: str) -> tuple[int, TokenType]:
    """verify the access token if possible to parse, 'signed' correct and is not expired

    Raises
    ------
    TokenError
        if not able to parse, signature wrong or expired

    """
    try:
        raw_token = base45.b45decode(token)
    except Exception as ex:
        log_and_raise_token_error(
            f"could not base45 decode token data: {ex}", code=b"Q"
        )

    try:
        user_id, expires, type_, _, signature = struct.unpack(
            f">IIH{settings.nonce_size}s{settings.digest_size}s", raw_token
        )
        data = raw_token[: -settings.digest_size]
        token_type = TokenType(type_)
        expires_datetime = datetime.utcfromtimestamp(expires)
    except Exception as ex:
        log_and_raise_token_error(f"could not unpack data: {ex}", code=b"Q")

    if not secrets.compare_digest(
        hashlib.shake_256(data + settings.secret).digest(settings.digest_size),
        signature,
    ):
        log_and_raise_token_error("could not verify signature", code=b"S")

    if datetime.utcnow() > expires_datetime:
        log_and_raise_token_error("token is expired", code=b"X")

    return user_id, token_type


if __name__ == "__main__":
    print(generate_access_token(1))
