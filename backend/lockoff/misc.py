import asyncio
import hashlib
import logging
import pathlib

from .config import settings

log = logging.getLogger(__name__)
lock = asyncio.Lock()
module_directory = pathlib.Path(__file__).resolve().parent


class DISPLAY_CODES:
    OK = b"K"
    GENERIC_ERROR = b"E"
    DAYTICKET_EXPIRED = b"D"
    NO_MEMBER = b"C"
    MORNING_OUTSIDE_HOURS = b"M"
    QR_ERROR = b"Q"
    QR_ERROR_SIGNATURE = b"S"
    QR_ERROR_EXPIRED = b"X"


class O_CMD:
    OK_SOUND = bytes([0x1B, 0x42, 0xD])
    OK_LED = bytes([0x1B, 0x4C, 0xD])
    ERROR_SOUND = bytes([0x1B, 0x45, 0xD])
    ERROR_LED = bytes([0x1B, 0x4E, 0xD])
    TRIGGER = bytes([0x1B, 0x5A, 0xD])
    DETRIGGER = bytes([0x1B, 0x59, 0xD])


from typing import AsyncIterator, TypeVar

T = TypeVar("T")


async def async_chunks(
    async_iterator: AsyncIterator[T],
    size: int,
) -> AsyncIterator[list[T]]:
    """Generate chunks from an asynchronous sequence.

    Chunks are lists consists of original ``T`` elements.
    The chunk can't contain more than ``size`` elements.
    The last chunk might contain less than ``size`` elements,
    but can't be empty.
    """
    finished = False

    while not finished:
        results: list[T] = []

        for _ in range(size):
            try:
                result = await anext(async_iterator)
            except StopAsyncIteration:
                finished = True
            else:
                results.append(result)

        if results:
            yield results


class Watchdog:
    def __init__(self):
        self._watch = []

    def watch(self, watch: asyncio.Task):
        self._watch.append(watch)

    def healthy(self):
        if any([w.done() for w in self._watch]):
            return False
        return True


watchdog = Watchdog()


def simple_hash(data: str) -> str:
    return hashlib.sha256(f"{data}{settings.hash_salt}".encode()).hexdigest()
