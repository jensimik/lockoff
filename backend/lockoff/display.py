import asyncio
import random
import serial_asyncio


class LCD:
    def __init__(self):
        self.queue = asyncio.Queue(maxsize=2)

    async def clear_screen(self):
        self.lcd_w.write(b"\xfe\x58")
        await self.lcd_w.drain()

    async def setup(self):
        _, self.lcd_w = await serial_asyncio.open_serial_connection()
        await self.clear_screen()

    def queue_message(self, line1: str, line2: str = None):
        self.queue.put_nowait((line1, line2))

    async def idle_message(self):
        # idle show "ready to scan" and random positions as "screensaver"
        idle_message = "ready to scan"
        await self.clear_screen()
        self.lcd_w.write(
            bytes(
                [
                    0xFE,
                    0x47,
                    random.randint(1, 3),
                    random.randint(1, 2),
                ]
            )
        )  # set random position
        self.lcd_w.write(idle_message.encode())
        await self.lcd_w.drain()

    async def runner(self):
        try:
            line1, line2 = await asyncio.wait_for(self.queue.get(), timeout=5)
            await self.clear_screen()
            self.lcd_w.write(line1.encode())
            if line2:
                self.lcd_w.write(bytes([0xFE, 0x47, 1, 2]))
                self.lcd_w.write(line2.encode())
            await self.lcd_w.drain()
            # show message for 5 seconds and then go back to idle
            await asyncio.sleep(5)
        except TimeoutError:
            pass
        finally:
            await self.idle_message()
