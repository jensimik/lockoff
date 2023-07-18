from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from ..depends import get_current_user_ids

router = APIRouter(tags=["card"])


@router.get("/card.pdf")
async def get_card_pdf(
    current_user_ids: Annotated[list[int], Depends(get_current_user_ids)]
):
    return current_user_ids
