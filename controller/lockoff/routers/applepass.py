import logging
from datetime import datetime
from typing import Annotated

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException, Response, status

from .. import schemas
from ..access_token import TokenMedia, TokenType, generate_access_token
from ..card import ApplePass
from ..config import settings
from ..db import DB, APDevice, APPass, APReg, User
from ..depends import apple_auth_pass

router = APIRouter(prefix="/v1", tags=["applepass"])

log = logging.getLogger(__name__)


@router.post(
    "/devices/{device_library_identifier}/registrations/{pass_type_identifier}/{serial_number}"
)
async def register_device(
    device_library_identifier: str,
    pass_type_identifier: str,
    serial_number: str,
    reg: schemas.AppleDeviceRegistration,
    current_pass: Annotated[dict, Depends(apple_auth_pass)],
):
    async with DB.transaction():
        # upsert device
        await APDevice.insert(
            APDevice(
                id=device_library_identifier,
                push_token=reg.pushToken,
            )
        ).on_conflict(
            target=APDevice.id,
            action="DO UPDATE",
            values=[APDevice.push_token],
        )
        # upsert link pass and device - piccolo-orm currently doesn't support compound-keys so cannot do upsert :-/
        update_tag = datetime.now(tz=settings.tz).isoformat(timespec="seconds")
        if not await APReg.exists().where(
            APReg.device_library_identifier == device_library_identifier,
            APReg.serial_number == serial_number,
        ):
            await APReg.insert(
                APReg(
                    device_library_identifier=device_library_identifier,
                    serial_number=serial_number,
                )
            )


@router.post(
    "/devices/{device_library_identifier}/registrations/{pass_type_identifier}/{serial_number}"
)
async def unregister_pass(
    device_library_identifier: str,
    pass_type_identifier: str,
    serial_number: str,
    current_pass: Annotated[dict, Depends(apple_auth_pass)],
):
    if await APPass.exists().where(APPass.serial_number == serial_number):
        async with DB.transaction():
            APPass.delete().where(APPass.serial_number == serial_number)
            APReg.delete().where(APReg.serial_number == serial_number)
    return {}


@router.get("/devices/{device_library_identifier}/registrations/{pass_type_identifier}")
async def get_list_of_updateable_passes_to_device(
    device_library_identifier: str,
    pass_type_identifier: str,
    passesUpdatedSince: int = 0,
):
    serial_numbers = (
        await APReg.select(APReg.serial_number)
        .output(as_list=True)
        .where(
            APReg.device_library_identifier == device_library_identifier,
            APReg.update_tag > passesUpdatedSince,
        )
    )
    if not serial_numbers:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)
    last_updated = datetime.now(tz=settings.tz).isoformat(timespec="seconds")
    return {"serialNumbers": serial_numbers, "lastUpdated": last_updated}


@router.get("/passes/{pass_type_identifier}/{serial_number}")
async def get_updated_pass(
    pass_type_identifier: str,
    serial_number: str,
    current_pass: Annotated[dict, Depends(apple_auth_pass)],
):
    user = await User.select().where(User.id == current_pass["user_id"]).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    access_token = generate_access_token(
        user_id=user["id"],
        token_type=TokenType(user["token_type"]),
        token_media=TokenMedia.DIGITAL,
    )
    expires_display = datetime.utcnow() + relativedelta(
        day=1, month=1, years=1, hour=0, minute=0, second=0, microsecond=0
    )
    serial = f"{settings.current_season}{user['id']}"
    pkpass_file = ApplePass.create(
        serial=serial,
        name=user["name"],
        level=TokenType(user["token_type"]).name.capitalize(),
        expires=expires_display,
        qr_code_data=access_token.decode(),
        update_auth_token=current_pass["update_auth_token"],
    )
    return Response(
        content=pkpass_file.getvalue(),
        media_type="application/vnd.apple.pkpass",
        headers={
            "Cache-Control": "no-cache",
            "CDN-Cache-Control": "no-store",
        },
    )


@router.post("/log")
async def log_message(aplog: schemas.AppleLog):
    for message in aplog.logs:
        log.info(message)
