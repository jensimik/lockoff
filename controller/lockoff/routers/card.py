import io
from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from tinydb import where

from lockoff import depends

from ..access_token import generate_access_token
from ..apple_pass import ApplePass
from ..config import settings
from ..db import DB_member
from ..paper_pass import generate_pdf

router = APIRouter(tags=["card"])


@router.get("/me")
async def me(mobile: Annotated[str, Depends(depends.get_current_mobile)]):
    async with DB_member as db:
        users = db.search((where("mobile") == mobile) & (where("active") == True))
    return [{"user_id": user.doc_id, "name": user["name"]} for user in users]


@router.get("/card-{user_id}.pdf")
async def get_card_pdf(
    user_id: int, mobile: Annotated[str, Depends(depends.get_current_mobile)]
):
    async with DB_member as db:
        user = db.get(doc_id=user_id)
    data = io.BytesIO()


@router.get("/card-{user_id}.pkpass")
async def get_pkpass(
    user_id: int, mobile: Annotated[str, Depends(depends.get_current_mobile)]
):
    return mobile
