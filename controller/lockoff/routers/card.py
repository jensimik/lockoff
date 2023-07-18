from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from tinydb import where

from lockoff import depends

from ..config import settings
from ..db import DB_member

router = APIRouter(tags=["card"])


@router.get("/me")
async def me(mobile: Annotated[str, Depends(depends.get_current_mobile)]):
    async with DB_member as db:
        users = db.search((where("mobile") == mobile) & (where("active") == True))

    pass


@router.get("/card.pdf")
async def get_card_pdf(mobile: Annotated[str, Depends(depends.get_current_mobile)]):
    return mobile


@router.get("/card.pkpass")
async def get_pkpass(mobile: Annotated[str, Depends(depends.get_current_mobile)]):
    return mobile
