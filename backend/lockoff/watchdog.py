import asyncio


class Watchdog:
    def __init__(self, watch):
        self.watch = watch

    # check if watched asyncio.Task's are still running every 30 seconds
    async def runner(self):
        while True:
            if not any([w.done() for w in self.watch]):
                # TODO: write to /dev/watchdog
                pass
            asyncio.sleep(30)
