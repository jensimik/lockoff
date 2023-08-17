import asyncio
import logging

import httpx
import serial_asyncio
from .config import settings
from .misc import DISPLAY_CODES, O_CMD, GFXDisplay, buzz_in

log = logging.getLogger(__name__)


class ReaderAuth(httpx.Auth):
    def auth_flow(self, request: httpx.Request):
        request.headers["reader-token"] = settings.reader_token
        yield request


class Reader:
    async def setup(self, display: GFXDisplay, url=settings.opticon_url):
        self.display = display
        self._r, self._w = await serial_asyncio.open_serial_connection(url=url)
        self.background_tasks = set()
        self.session = httpx.AsyncClient(auth=ReaderAuth())

    # write opticon command to serial
    async def o_cmd(self, cmds: list[bytes]):
        for cmd in cmds:
            self._w.write(cmd)
        await self._w.drain()

    async def runner(self, one_time_run: bool = False):
        while True:
            # read a scan from the barcode reader read until carriage return CR
            qr_code: str = (
                (await self._r.readuntil(separator=b"\r")).decode("utf-8").strip()
            )
            try:
                # check the qr_code
                response = await self.session.post(
                    settings.backend_url, json={"qr_code": qr_code}, timeout=5
                )
                if response.is_success:
                    # buzz in
                    task = asyncio.create_task(buzz_in())
                    self.background_tasks.add(task)
                    task.add_done_callback(self.background_tasks.discard)
                    # show OK on display
                    await self.display.send_message(DISPLAY_CODES.OK)
                    # give good sound+led on opticon now qr code is verified
                    await self.o_cmd(cmds=[O_CMD.OK_SOUND, O_CMD.OK_LED])
                else:
                    # if error then get the 418 teapot error in the json detail
                    data = response.json().get("detail", {})
                    await self.display.send_message(
                        data.get(
                            "error_code", DISPLAY_CODES.GENERIC_ERROR.decode()
                        ).encode()
                    )
                    await self.o_cmd(cmds=[O_CMD.ERROR_SOUND, O_CMD.ERROR_LED])
            # generic error? show system error on display
            except Exception:
                log.exception(f"generic error in reader {ex}")
                await self.display.send_message(DISPLAY_CODES.GENERIC_ERROR)
                await self.o_cmd(cmds=[O_CMD.ERROR_SOUND, O_CMD.ERROR_LED])
            # one_time_run is used for testing
            if one_time_run:
                break
