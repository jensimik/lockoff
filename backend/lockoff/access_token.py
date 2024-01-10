import base64
import hashlib
import logging
import secrets
import struct
from datetime import datetime
from enum import Enum, IntFlag

import base45
from dateutil.relativedelta import relativedelta
from fastapi import HTTPException, status

from .config import settings
from .misc import DISPLAY_CODES

log = logging.getLogger(__name__)
door_log = logging.getLogger("door")


class TokenType(Enum):
    NORMAL = 1
    OFFPEAK = 2
    DAY_TICKET = 3
    JUNIOR_HOLD = 4
    BØRNE_HOLD = 5
    # MINI_HOLD = 6
    OTHER = 9


class TokenMedia(IntFlag):
    UNKNOWN = 0
    PRINT = 1
    DIGITAL = 2
    ANDROID = 4
    APPLE = 8


class TokenError(Exception):
    def __init__(self, message, code=DISPLAY_CODES.QR_ERROR):
        super().__init__(message)
        self.code = code


def log_and_raise_token_error(message, code=DISPLAY_CODES.QR_ERROR, level=logging.WARN):
    log.log(level=level, msg=message)
    raise TokenError(message, code=code)


def generate_access_token(
    user_id: int,
    token_type: TokenType = TokenType.NORMAL,
    token_media: TokenMedia = TokenMedia.PRINT,
    expire_delta: relativedelta = relativedelta(
        day=1, month=1, years=1, hour=1, minute=0, second=0, microsecond=0
    ),
) -> bytes:
    """Generate a new access token
    the access token should be used as data in a QR code
    the QR code can be printed or used in apple/google wallet as a memebership card

    Returns
    -------
    bytes
        the base45 encoded token

    """

    expire = datetime.now(tz=settings.tz) + expire_delta
    data = struct.pack(
        ">IIHH",
        user_id,
        int(expire.timestamp()),
        token_type.value,
        token_media.value,
    )

    nonce = secrets.token_bytes(settings.nonce_size)

    signature = hashlib.shake_256(data + nonce + settings.secret).digest(
        settings.digest_size
    )

    return base45.b45encode(data + nonce + signature)


def verify_access_token(token: str) -> tuple[int, TokenType, TokenMedia, str]:
    """verify the access token if possible to parse, 'signed' correct and is not expired

    Raises
    ------
    TokenError
        if not able to parse, signature wrong or expired

    """
    try:
        raw_token = base45.b45decode(token[:39])
        totp_suffix = token[39:]
    except Exception as ex:
        log_and_raise_token_error(
            f"could not base45 decode token data: {ex}", code=DISPLAY_CODES.QR_ERROR
        )

    try:
        user_id, expires, type_, media_, _, signature = struct.unpack(
            f">IIHH{settings.nonce_size}s{settings.digest_size}s",
            raw_token[: 12 + settings.nonce_size + settings.digest_size],
        )
        token_type = TokenType(type_)
        token_media = TokenMedia(media_)
        data = raw_token[: -settings.digest_size]
        # android have 8 digit totp in the token suffix
        expires_datetime = datetime.fromtimestamp(expires, tz=settings.tz)
    except Exception as ex:
        log_and_raise_token_error(
            f"could not unpack data: {ex}", code=DISPLAY_CODES.QR_ERROR
        )

    if not secrets.compare_digest(
        hashlib.shake_256(data + settings.secret).digest(settings.digest_size),
        signature,
    ):
        log_and_raise_token_error(
            "could not verify signature", code=DISPLAY_CODES.QR_ERROR_SIGNATURE
        )

    if datetime.now(tz=settings.tz) > expires_datetime:
        log_and_raise_token_error(
            "token is expired", code=DISPLAY_CODES.QR_ERROR_EXPIRED
        )

    print(f"totp_suffix {totp_suffix}")

    return user_id, token_type, token_media, totp_suffix


def _generate_dl_token(
    user_id: int, scope: int, expire_delta: relativedelta = relativedelta(hours=2)
):
    expires = int((datetime.now(tz=settings.tz) + expire_delta).timestamp())
    data = struct.pack(">IHI", user_id, scope, expires)
    nonce = secrets.token_bytes(settings.dl_nonce_size)
    signature = hashlib.shake_256(data + nonce + settings.dl_secret).digest(
        settings.dl_digest_size
    )
    return base64.urlsafe_b64encode(data + nonce + signature).decode("utf-8")


def _verify_dl_token(token: str, required_scope: int) -> int:
    token_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail="could not verify signature or link has expired",
    )
    try:
        raw_token = base64.urlsafe_b64decode(token)
        user_id, scope, expires, _, signature = struct.unpack(
            f">IHI{settings.dl_nonce_size}s{settings.dl_digest_size}s", raw_token
        )
        data = raw_token[: -settings.dl_digest_size]
        if scope != required_scope:
            raise token_exception
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


# this token is only for download of pdf/pkpass files - signed with user and expire time set to two hours
def generate_dl_member_token(
    user_id: int,
    expire_delta: relativedelta = relativedelta(hours=2),
) -> str:
    return _generate_dl_token(user_id=user_id, scope=1, expire_delta=expire_delta)


# depends for download files - see below
def verify_dl_member_token(token: str) -> int:
    return _verify_dl_token(token=token, required_scope=1)


# this token is only for download of pdf/pkpass files - signed with user and expire time set to two hours
def generate_dl_admin_token(
    user_id: int,
    expire_delta: relativedelta = relativedelta(hours=2),
) -> str:
    return _generate_dl_token(user_id=user_id, scope=2, expire_delta=expire_delta)


# depends for download files - see below
def verify_dl_admin_token(token: str) -> int:
    return _verify_dl_token(token=token, required_scope=2)
