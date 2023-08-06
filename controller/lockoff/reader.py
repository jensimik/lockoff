import asyncio
import logging
from datetime import datetime

import serial_asyncio
from dateutil.relativedelta import relativedelta

from .access_token import (
    TokenError,
    TokenType,
    log_and_raise_token_error,
    verify_access_token,
)
from .config import settings
from .db import DB, Dayticket, User, AccessLog
from .misc import DISPLAY_CODES, O_CMD, GFXDisplay, buzz_in

log = logging.getLogger(__name__)


async def check_member(user_id: int, member_type: TokenType):
    user = await User.select(User.id).where(User.id == user_id).first()
    if not user:
        log_and_raise_token_error(
            "did you cancel your membership?", code=DISPLAY_CODES.NO_MEMBER
        )
    if member_type == TokenType.MORNING:
        # TODO: check if morning member has access in current hour?
        pass


async def check_dayticket(user_id: int):
    if ticket := await Dayticket.select().where(Dayticket.id == user_id).first():
        if ticket["expires"] == 0:
            # first use - set expire at midnight of current day
            expire = datetime.now(tz=settings.tz) + relativedelta(
                hour=23, minute=59, second=59, microsecond=0
            )
            async with DB.transaction():
                await Dayticket.update(
                    {Dayticket.expires: int(expire.timestamp())}
                ).where(Dayticket.id == user_id)
        elif datetime.now(tz=settings.tz) > datetime.fromtimestamp(
            ticket["expires"], tz=settings.tz
        ):
            log_and_raise_token_error(
                "dayticket is expired", code=DISPLAY_CODES.DAYTICKET_EXPIRED
            )


async def check_qrcode(qr_code: str):
    user_id, token_type = verify_access_token(
        token=qr_code
    )  # it will raise TokenError if not valid
    log.info(f"checking user {user_id} {token_type}")
    # check in database
    match token_type:
        case TokenType.NORMAL | TokenType.MORNING:
            await check_member(user_id=user_id, member_type=token_type)
        case TokenType.DAY_TICKET:
            await check_dayticket(user_id=user_id)
    log.info(f"{user_id} {token_type} access granted")
    # log in access_log db
    async with DB.transaction():
        await AccessLog.insert(
            AccessLog(
                id=None,
                obj_id=user_id,
                token_type=token_type,
                timestamp=datetime.now(tz=settings.tz).isoformat(timespec="seconds"),
            )
        )


class Reader:
    async def setup(self, display: GFXDisplay, url=settings.opticon_url):
        self.display = display
        self._r, self._w = await serial_asyncio.open_serial_connection(url=url)
        self.background_tasks = set()

    # write opticon command to serial
    async def o_cmd(self, cmds: list[bytes]):
        for cmd in cmds:
            self._w.write(cmd)
        await self._w.drain()

    async def runner(self, one_time_run: bool = False):
        while True:
            # read a scan from the barcode reader read until carriage return CR
            qr_code = (await self._r.readuntil(separator=b"\r")).decode("utf-8").strip()
            try:
                # check the qr_code (raises exception on errors)
                await check_qrcode(qr_code=qr_code)
                # buzz in
                task = asyncio.create_task(buzz_in())
                self.background_tasks.add(task)
                task.add_done_callback(self.background_tasks.discard)
                # show OK on display
                await self.display.send_message(DISPLAY_CODES.OK)
                # give good sound+led on opticon now qr code is verified
                await self.o_cmd(cmds=[O_CMD.OK_SOUND, O_CMD.OK_LED])
            except TokenError as ex:
                # show error message on display
                log.warning(ex)
                await self.display.send_message(ex.code)
                await self.o_cmd(cmds=[O_CMD.ERROR_SOUND, O_CMD.ERROR_LED])
            # generic error? show system error on display
            except Exception:
                log.exception("generic error in reader")
                await self.display.send_message(DISPLAY_CODES.GENERIC_ERROR)
                await self.o_cmd(cmds=[O_CMD.ERROR_SOUND, O_CMD.ERROR_LED])
            # one_time_run is used for testing
            if one_time_run:
                break
