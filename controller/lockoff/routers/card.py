from typing import Annotated

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status

from ..depends import get_current_mobile

router = APIRouter(tags=["card"])


@router.get("/card.pdf")
async def get_card_pdf(
    current_mobile: Annotated[list[int], Depends(get_current_mobile)]
):
    return current_mobile
