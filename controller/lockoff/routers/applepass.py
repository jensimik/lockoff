import logging
from datetime import datetime, timezone
from typing import Annotated

from dateutil.relativedelta import relativedelta
from fastapi import APIRouter, Depends, HTTPException, Response, status
from email.utils import formatdate

from .. import schemas
from ..access_token import TokenMedia, TokenType, generate_access_token
from ..card import ApplePass
from ..config import settings
from ..db import DB, APDevice, APPass, APReg, User
from ..depends import apple_auth_pass

router = APIRouter(prefix="/v1", tags=["applepass"])

log = logging.getLogger(__name__)


# apple wallet registration
@router.post(
    "/devices/{device_library_identifier}/registrations_attido/{pass_type_identifier}/{serial_number}"
)
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
                device_type=current_pass["scheme"],
                push_service_url=reg.pushServiceUrl,
            )
        ).on_conflict(
            target=APDevice.id,
            action="DO UPDATE",
            values=[
                APDevice.push_token,
                APDevice.device_type,
                APDevice.push_service_url,
            ],
        )
        # upsert link pass and device - piccolo-orm currently doesn't support compound-keys so cannot do upsert :-/
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


# apple wallet delete
@router.delete(
    "/devices/{device_library_identifier}/registrations/{pass_type_identifier}/{serial_number}"
)
async def unregister_pass(
    device_library_identifier: str,
    pass_type_identifier: str,
    serial_number: str,
    current_pass: Annotated[dict, Depends(apple_auth_pass)],
):
    async with DB.transaction():
        await APReg.delete().where(
            APReg.serial_number == serial_number,
            APReg.device_library_identifier == device_library_identifier,
        )
        if not APReg.exists().where(APReg.serial_number == serial_number):
            APPass.delete().where(APPass.serial_number == serial_number)
    return {}


# apple wallet get available passes for this device
@router.get("/devices/{device_library_identifier}/registrations/{pass_type_identifier}")
async def get_list_of_updateable_passes_to_device(
    device_library_identifier: str,
    pass_type_identifier: str,
    passesUpdatedSince: str = "",
):
    query = APReg.select(
        APReg.serial_number, APReg.serial_number.join_on(APPass.id).update_tag
    ).where(APReg.device_library_identifier == device_library_identifier)
    if passesUpdatedSince:
        query = query.where(APPass.update_tag > passesUpdatedSince)
    data = await query
    last_updated = sorted([d["update_tag"] for d in data], reverse=True)[0]
    serial_numbers = [d["serial_number"] for d in data]
    if not serial_numbers:
        raise HTTPException(status_code=status.HTTP_204_NO_CONTENT)
    return {"serialNumbers": serial_numbers, "lastUpdated": last_updated}


# apple wallet get updated pass
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
        update_auth_token=current_pass["auth_token"],
    )
    tmplm = datetime.fromisoformat(current_pass["update_tag"])
    last_modified = formatdate(
        tmplm.astimezone(tz=timezone.utc).timestamp(), usegmt=True
    )
    return Response(
        content=pkpass_file.getvalue(),
        media_type="application/vnd.apple.pkpass",
        headers={
            "Cache-Control": "no-cache",
            "CDN-Cache-Control": "no-store",
            "last-modified": last_modified,
        },
    )


# apple wallet show log info
@router.post("/log")
async def log_message(aplog: schemas.AppleLog):
    for message in aplog.logs:
        log.info(message)
