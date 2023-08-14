import json
import logging

from fastapi import APIRouter, Request

from ..card import GPassStatus
from ..db import GPass

router = APIRouter(tags=["google_wallet"])

log = logging.getLogger(__name__)


@router.post("/callback")
async def callback(request: Request):
    # TODO: verify signature!
    data = request.json()
    event = json.loads(data["signedMessage"])
    _, pass_id = event["objectId"].split(".")
    event_type = event["eventType"]
    status = (
        GPassStatus.SAVED
        if event_type == "save"
        else GPassStatus.DELETED
        if event_type == "del"
        else GPassStatus.UNKNOWN
    )
    await GPass.update({GPass.status: status}).where(GPass.id == pass_id)
