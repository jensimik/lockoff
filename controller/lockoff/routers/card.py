from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from ..db import DB_member
from tinydb import where

from ..depends import get_current_mobile

router = APIRouter(tags=["card"])


@router.post("/generate-cards")
async def generate_cards(
    current_mobile: Annotated[list[int], Depends(get_current_mobile)]
):
    async with DB_member as db:
        users = db.search(
            (where("mobile") == current_mobile) & (where("active") == True)
        )
    for user in users:
        pass


@router.get("/card.pdf")
async def get_card_pdf(
    current_mobile: Annotated[list[int], Depends(get_current_mobile)]
):
    return current_mobile
