import logging
from datetime import datetime

from fastapi import APIRouter, HTTPException, status

from .. import schemas
from ..db import DB, APDevice, APPass, APReg
from ..config import settings

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
):
    async with DB.transaction():
        # upsert device
        await APDevice.insert(
            APDevice(
                device_library_identifier=device_library_identifier,
                push_token=reg.push_token,
            )
        ).on_conflict(
            target=APDevice.device_library_identifier,
            action="DO UPDATE",
            values=[APDevice.push_token],
        )
        # upsert pass
        await APPass.insert(APPass(serial_number=serial_number)).on_conflict(
            target=APPass.serial_number, action="DO NOTHING"
        )
        # upsert link pass and device
        await APReg.insert(
            APReg(
                device_library_identifier=device_library_identifier,
                serial_number=serial_number,
            )
        ).on_conflict(action="DO NOTHING")


@router.post(
    "/devices/{device_library_identifier}/registrations/{pass_type_identifier}/{serial_number}"
)
async def unregister_pass(
    device_library_identifier: str, pass_type_identifier: str, serial_number: str
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
async def get_updated_pass(pass_type_identifier: str, serial_number: str):
    pass
