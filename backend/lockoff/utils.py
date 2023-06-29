import asyncio

# import gpiozero
from pydantic.dataclasses import dataclass

# relay = gpiozero.DigitalOutputDevice(22)
relay_lock = asyncio.Lock()


async def relay_buzz():
    async with relay_lock:
        # relay.on()
        asyncio.sleep(4)
        # relay.off()
