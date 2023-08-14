import base64
import io
import secrets
from datetime import datetime
from typing import Annotated

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import RedirectResponse

from ..access_token import (
    TokenMedia,
    TokenType,
    generate_access_token,
    verify_dl_member_token,
)
from ..card import ApplePass, GooglePass, generate_pdf, generate_png
from ..config import settings
from ..db import DB, APPass, GPass, User

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
        user_id=user["id"],
        token_type=TokenType(user["token_type"]),
        token_media=TokenMedia.UNKNOWN,
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
        user_id=user["id"],
        token_type=TokenType(user["token_type"]),
        token_media=TokenMedia.PRINT,
    )
    pdf_file = generate_pdf(
        user_id=user["id"],
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
        user_id=user["id"],
        token_type=TokenType(user["token_type"]),
        token_media=TokenMedia.DIGITAL | TokenMedia.APPLE,
    )
    expires_display = datetime.utcnow() + relativedelta(
        day=1, month=1, years=1, hour=0, minute=0, second=0, microsecond=0
    )
    serial = f"{settings.current_season}{user_id}"
    # check if already issued? - then use the same auth_token
    update_auth_token = secrets.token_hex(64)
    if (
        current_pass := await APPass.select(APPass.auth_token)
        .where(APPass.id == serial)
        .first()
    ):
        update_auth_token = current_pass["auth_token"]
    # generate the apple pass
    pkpass_file = ApplePass.create(
        serial=serial,
        name=user["name"],
        level=TokenType(user["token_type"]).name.capitalize(),
        expires=expires_display,
        qr_code_data=access_token.decode(),
        update_auth_token=update_auth_token,
    )
    async with DB.transaction():
        # mark that the user have downloaded pkpass/digital for this season
        await User.update({User.season_digital: str(settings.current_season)}).where(
            User.id == user_id
        )
        # create a tracked appass
        await APPass.insert(
            APPass(
                id=serial, auth_token=update_auth_token, user_id=user_id, update_tag=0
            )
        ).on_conflict(target=APPass.id, action="DO UPDATE", values=[APPass.update_tag])

    return Response(
        content=pkpass_file.getvalue(),
        media_type="application/vnd.apple.pkpass",
        headers={
            "Content-Disposition": f'attachment; filename="nkk-card-{user_id}.pkpass"',
            "Cache-Control": "no-cache",
            "CDN-Cache-Control": "no-store",
        },
    )


# digital google wallet pass (jwt)
@router.get(
    "/{token}/membership-card",
    response_class=Response,
)
async def get_google_wallet(
    user_id: Annotated[int, Depends(verify_dl_member_token)],
):
    user = await User.select().where(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)
    access_token = generate_access_token(
        user_id=user["id"],
        token_type=TokenType(user["token_type"]),
        token_media=TokenMedia.DIGITAL | TokenMedia.ANDROID,
    )
    expires_display = datetime.utcnow() + relativedelta(
        day=1, month=1, years=1, hour=0, minute=0, second=0, microsecond=0
    )
    serial = f"{settings.current_season}{user_id}"
    totp_key = secrets.token_hex(16)
    async with GooglePass() as gp:
        jwt_url = gp.create_pass(
            pass_id=serial,
            name=user["name"],
            level=TokenType(user["token_type"]).name.capitalize(),
            expires=expires_display,
            qr_code_data=access_token.decode(),
            totp_key=totp_key,
        )
    async with DB.transaction():
        # mark that the user have downloaded digital for this season
        await User.update({User.season_digital: str(settings.current_season)}).where(
            User.id == user_id
        )
        # create a tracked gpass
        await GPass.insert(
            GPass(id=serial, totp=totp_key, user_id=user_id)
        ).on_conflict(target=GPass.id, action="DO UPDATE", values=[GPass.totp])
    return RedirectResponse(
        url=jwt_url,
        headers={"Cache-Control": "no-cache", "CDN-Cache-Control": "no-store"},
    )
