import base64
import hashlib
import logging
import secrets
import struct
from datetime import datetime
from enum import Enum

import base45
from dateutil.relativedelta import relativedelta
from fastapi import HTTPException, status

from .config import settings

log = logging.getLogger(__name__)
door_log = logging.getLogger("door")


class TokenType(Enum):
    NORMAL = 1
    MORNING = 2
    DAY_TICKET = 3


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
        ">IIH",
        user_id,
        int(expire.timestamp()),
        token_type.value,
    )

    nonce = secrets.token_bytes(settings.nonce_size)

    signature = hashlib.shake_256(data + nonce + settings.secret).digest(
        settings.digest_size
    )

    return base45.b45encode(data + nonce + signature)


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
        expires_datetime = datetime.fromtimestamp(expires, tz=settings.tz)
    except Exception as ex:
        log_and_raise_token_error(f"could not unpack data: {ex}", code=b"Q")

    if not secrets.compare_digest(
        hashlib.shake_256(data + settings.secret).digest(settings.digest_size),
        signature,
    ):
        log_and_raise_token_error("could not verify signature", code=b"S")

    if datetime.now(tz=settings.tz) > expires_datetime:
        log_and_raise_token_error("token is expired", code=b"X")

    return user_id, token_type


# this token is only for download of pdf/pkpass files - signed with user and expire time set to two hours
def generate_dl_token(
    user_id: int,
    expire_delta: relativedelta = relativedelta(hours=2),
) -> str:
    expires = int((datetime.now(tz=settings.tz) + expire_delta).timestamp())
    data = struct.pack(">II", user_id, expires)
    nonce = secrets.token_bytes(settings.dl_nonce_size)
    signature = hashlib.shake_256(data + nonce + settings.dl_secret).digest(
        settings.dl_digest_size
    )
    return base64.urlsafe_b64encode(data + nonce + signature).decode("utf-8")


# depends for download files - see below
def verify_dl_token(token: str) -> int:
    token_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="could not verify signature or link has expired",
    )
    try:
        raw_token = base64.urlsafe_b64decode(token)
        user_id, expires, _, signature = struct.unpack(
            f">II{settings.dl_nonce_size}s{settings.dl_digest_size}s", raw_token
        )
        data = raw_token[: -settings.dl_digest_size]
        expires_datetime = datetime.fromtimestamp(expires, tz=settings.tz)
        if not secrets.compare_digest(
            hashlib.shake_256(data + settings.dl_secret).digest(
                settings.dl_digest_size
            ),
            signature,
        ):
            raise token_exception
        if datetime.now(tz=settings.tz) > expires_datetime:
            raise token_exception
    except Exception:
        raise token_exception
    return user_id


if __name__ == "__main__":
    print(generate_access_token(1))
