import asyncio
import enum

# import gpiozero
from pydantic.dataclasses import dataclass


class TokenEnum(enum.Enum):
    full = 1
    morning = 2
    special = 3
    denied = 99


@dataclass
class Member:
    name: str
    token_type: TokenEnum
    token: str


# relay = gpiozero.DigitalOutputDevice(22)
relay_lock = asyncio.Lock()


async def relay_buzz():
    async with relay_lock:
        # relay.on()
        asyncio.sleep(4)
        # relay.off()
