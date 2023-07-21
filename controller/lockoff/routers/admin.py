from datetime import datetime
from typing import Annotated

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, HTTPException, Response, Security, status

from lockoff import depends

from ..access_token import TokenType, generate_access_token
from ..apple_pass import ApplePass
from ..config import settings
from ..db import queries
from ..depends import DBcon

router = APIRouter(tags=["admin"])


@router.get("/access_log")
async def access_log(
    mobile: Annotated[str, Security(depends.get_current_mobile, scopes=["admin"])],
    conn: DBcon,
):
    return await queries.last_log_entries(conn, limit=30)
