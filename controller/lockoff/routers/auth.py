from fastapi import APIRouter, BackgroundTasks, HTTPException, status

router = APIRouter(tags=["auth"])


@router.post("/login")
async def login():
    pass
