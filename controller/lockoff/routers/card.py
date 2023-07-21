from datetime import datetime
from typing import Annotated

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException, Response, status

from ..access_token import TokenType, generate_access_token, verify_dl_token
from ..apple_pass import ApplePass
from ..config import settings
from ..db import queries
from ..depends import DBcon
from ..paper_pass import generate_pdf

router = APIRouter(tags=["card"])


# pdf membership card ready to print
@router.get(
    "/{token}/membership-card.pdf",
    response_class=Response,
    responses={
        200: {"content": {"application/pdf": {}}},
    },
)
async def get_card_pdf(
    user_id: Annotated[int, Depends(verify_dl_token)],
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


# pkpass is for apple wallet direct (and mobilewallet on android)
@router.get(
    "/{token}/membership-card.pkpass",
    response_class=Response,
    responses={
        200: {"content": {"application/vnd.apple.pkpass": {}}},
    },
)
async def get_pkpass(
    user_id: Annotated[int, Depends(verify_dl_token)],
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
