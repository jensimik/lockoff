from datetime import datetime
from typing import Annotated

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException, Response, status
from tinydb import where

from lockoff import depends

from ..access_token import TokenType, generate_access_token
from ..apple_pass import ApplePass
from ..config import settings
from ..db import queries
from ..depends import DBcon
from ..paper_pass import generate_pdf

router = APIRouter(tags=["card"])


@router.get("/me")
async def me(mobile: Annotated[str, Depends(depends.get_current_mobile)], conn: DBcon):
    users = await queries.get_active_users_by_mobile(conn, mobile=mobile)
    return [{"user_id": user["user_id"], "name": user["name"]} for user in users]


@router.get(
    "/membership-card-{user_id}.pdf",
    response_class=Response,
    responses={
        200: {"content": {"application/pdf": {}}},
    },
)
async def get_card_pdf(
    user_id: int,
    mobile: Annotated[str, Depends(depends.get_current_mobile)],
    conn: DBcon,
):
    user = await queries.get_active_users_by_user_id_mobile(
        conn, user_id=user_id, mobile=mobile
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    token_type = (
        TokenType.MORNING if user["member_type"] == "MORN" else TokenType.NORMAL
    )
    access_token = generate_access_token(user_id=user.doc_id, token_type=token_type)
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
    "/membership-card-{user_id}.pkpass",
    response_class=Response,
    responses={
        200: {"content": {"application/vnd.apple.pkpass": {}}},
    },
)
async def get_pkpass(
    user_id: int,
    mobile: Annotated[str, Depends(depends.get_current_mobile)],
    conn: DBcon,
):
    user = await queries.get_active_users_by_user_id_mobile(
        conn, user_id=user_id, mobile=mobile
    )
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    token_type = (
        TokenType.MORNING if user["member_type"] == "MORN" else TokenType.NORMAL
    )
    access_token = generate_access_token(user_id=user.doc_id, token_type=token_type)
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
