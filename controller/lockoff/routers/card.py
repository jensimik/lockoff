from fastapi import APIRouter, BackgroundTasks, HTTPException, status

router = APIRouter(tags=["card"])


@router.get("/card.pdf")
async def get_card_pdf():
    pass
