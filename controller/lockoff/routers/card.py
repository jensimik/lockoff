import hashlib
import struct
import secrets
import base45
import calendar
from datetime import datetime
from typing import Annotated

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException, Response, Security, status

from lockoff import depends

from ..access_token import TokenType, generate_access_token
from ..apple_pass import ApplePass
from ..config import settings
from ..db import queries
from ..depends import DBcon
from ..paper_pass import generate_pdf

router = APIRouter(tags=["card"])


def generate_token(
    user_id: int,
    expire_delta: relativedelta = relativedelta(hour=2),
) -> str:
    expires = datetime.utcnow() + expire_delta
    data = struct.pack(">II", user_id, calendar.timegm(expires.utctimetuple()))
    nonce = secrets.token_bytes(settings.nonce_size)
    signature = hashlib.shake_256(data + nonce + settings.secret).digest(
        settings.digest_size
    )
    return base45.b45encode(data + nonce + signature).decode("utf-8")


def verify_token(token: str) -> int:
    token_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="could not verify signature"
    )
    try:
        raw_token = base45.b45decode(token)
        print(f"raw token {raw_token}")
        user_id, expires, _, signature = struct.unpack(
            f">II{settings.nonce_size}s{settings.digest_size}s", raw_token
        )
        print(f"user_id {user_id} expires {expires}")
        data = raw_token[: -settings.digest_size]
        expires_datetime = datetime.utcfromtimestamp(expires)
        print(f"expires datetime {expires_datetime}")
        if not secrets.compare_digest(
            hashlib.shake_256(data + settings.secret).digest(settings.digest_size),
            signature,
        ):
            print("signature wrong?")
            raise token_exception
        if datetime.utcnow() > expires_datetime:
            print("expired")
            raise token_exception
    except Exception:
        raise token_exception
    return user_id


@router.get("/me")
async def me(
    mobile: Annotated[str, Security(depends.get_current_mobile, scopes=["basic"])],
    conn: DBcon,
):
    users = await queries.get_active_users_by_mobile(conn, mobile=mobile)
    return [
        {
            "user_id": user["user_id"],
            "name": user["name"],
            "token": generate_token(user["user_id"]),
        }
        for user in users
    ]


@router.get(
    "/membership-card-{token}.pdf",
    response_class=Response,
    responses={
        200: {"content": {"application/pdf": {}}},
    },
)
async def get_card_pdf(
    user_id: Annotated[int, Depends(verify_token)],
    conn: DBcon,
):
    user = await queries.get_active_users_by_user_id(conn, user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    token_type = (
        TokenType.MORNING if user["member_type"] == "MORN" else TokenType.NORMAL
    )
    access_token = generate_access_token(user_id=user["user_id"], token_type=token_type)
    pdf_file = generate_pdf(
        name=user["name"],
        level=f"{token_type.name.capitalize()} {settings.current_season}",
        qr_code_data=access_token,
    )
    return Response(
        content=pdf_file.getvalue(),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="nkk-card-{user_id}.pdf"',
            "Cache-Control": "no-cache",
            "CDN-Cache-Control": "no-store",
        },
    )


@router.get(
    "/membership-card-{token}.pkpass",
    response_class=Response,
    responses={
        200: {"content": {"application/vnd.apple.pkpass": {}}},
    },
)
async def get_pkpass(
    user_id: Annotated[int, Depends(verify_token)],
    conn: DBcon,
):
    user = await queries.get_active_users_by_user_id(conn, user_id=user_id)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    token_type = (
        TokenType.MORNING if user["member_type"] == "MORN" else TokenType.NORMAL
    )
    access_token = generate_access_token(user_id=user["user_id"], token_type=token_type)
    expires_display = datetime.utcnow() + relativedelta(
        day=1, month=1, years=1, hour=0, minute=0, second=0, microsecond=0
    )
    pkpass_file = ApplePass.create(
        user_id=user_id,
        name=user["name"],
        level=token_type.name.capitalize(),
        expires=expires_display,
        qr_code_data=access_token.decode("utf-8"),
    )
    return Response(
        content=pkpass_file.getvalue(),
        media_type="application/vnd.apple.pkpass",
        headers={
            "Content-Disposition": f'attachment; filename="nkk-card-{user_id}.pkpass"',
            "Cache-Control": "no-cache",
            "CDN-Cache-Control": "no-store",
        },
    )
