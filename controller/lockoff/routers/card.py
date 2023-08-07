import io
from datetime import datetime
from typing import Annotated

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException, Response, status

from ..access_token import TokenType, generate_access_token, verify_dl_member_token
from ..card import ApplePass, generate_pdf, generate_png
from ..config import settings
from ..db import User, DB

router = APIRouter(tags=["card"])


@router.get(
    "/{token}/qr-code.png",
    response_class=Response,
    responses={
        200: {"content": {"image/png": {}}},
    },
)
async def get_qr_code_png(
    user_id: Annotated[int, Depends(verify_dl_member_token)],
):
    user = await User.select().where(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    access_token = generate_access_token(
        user_id=user["id"], token_type=TokenType(user["token_type"])
    )
    img = generate_png(qr_code_data=access_token.decode())
    with io.BytesIO() as f:
        img.save(f, format="png")
        content = f.getvalue()
    return Response(content=content, media_type="image/png")


# pdf membership card ready to print
@router.get(
    "/{token}/membership-card.pdf",
    response_class=Response,
    responses={
        200: {"content": {"application/pdf": {}}},
    },
)
async def get_card_pdf(
    user_id: Annotated[int, Depends(verify_dl_member_token)],
):
    user = await User.select().where(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    access_token = generate_access_token(
        user_id=user["id"], token_type=TokenType(user["token_type"])
    )
    pdf_file = generate_pdf(
        name=user["name"],
        level=f"{TokenType(user['token_type']).name.capitalize()} {settings.current_season}",
        qr_code_data=access_token.decode(),
    )
    # mark that the user have downloaded pdf/print for this season
    async with DB.transaction():
        await User.update({User.season_print: str(settings.current_season)}).where(
            User.id == user_id
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
    user_id: Annotated[int, Depends(verify_dl_member_token)],
):
    user = await User.select().where(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    access_token = generate_access_token(
        user_id=user["id"], token_type=TokenType(user["token_type"])
    )
    expires_display = datetime.utcnow() + relativedelta(
        day=1, month=1, years=1, hour=0, minute=0, second=0, microsecond=0
    )
    pkpass_file = ApplePass.create(
        user_id=user_id,
        name=user["name"],
        level=TokenType(user["token_type"]).name.capitalize(),
        expires=expires_display,
        qr_code_data=access_token.decode(),
    )
    # mark that the user have downloaded pkpass/digital for this season
    async with DB.transaction():
        await User.update({User.season_digital: str(settings.current_season)}).where(
            User.id == user_id
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
