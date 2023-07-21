import base64
import hashlib
import secrets
import struct
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
    expire_delta: relativedelta = relativedelta(hours=2),
) -> str:
    expires = int((datetime.now(tz=settings.tz) + expire_delta).timestamp())
    data = struct.pack(">II", user_id, expires)
    nonce = secrets.token_bytes(settings.nonce_size)
    signature = hashlib.shake_256(data + nonce + settings.secret).digest(
        settings.dl_digest_size
    )
    return base64.urlsafe_b64encode(data + nonce + signature).decode("utf-8")


def verify_token(token: str) -> int:
    token_exception = HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST, detail="could not verify signature"
    )
    try:
        raw_token = base64.urlsafe_b64decode(token)
        user_id, expires, _, signature = struct.unpack(
            f">II{settings.nonce_size}s{settings.dl_digest_size}s", raw_token
        )
        data = raw_token[: -settings.dl_digest_size]
        expires_datetime = datetime.fromtimestamp(expires, tz=settings.tz)
        if not secrets.compare_digest(
            hashlib.shake_256(data + settings.secret).digest(settings.dl_digest_size),
            signature,
        ):
            raise token_exception
        if datetime.now(tz=settings.tz) > expires_datetime:
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
    "/{token}/membership-card.pdf",
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
    "/{token}/membership-card.pkpass",
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
