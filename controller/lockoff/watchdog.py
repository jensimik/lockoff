import asyncio


class Watchdog:
    def __init__(self):
        self.watch = []

    def watch(self, watch: asyncio.Task):
        self.watch.append(watch)

    def healthy(self):
        if any([w.done() for w in self.watch]):
            return False
        return True

    # check if watched asyncio.Task's are still running every 30 seconds
    async def runner(self):
        while True:
            if self.healthy():
                # TODO: write to /dev/watchdog
                pass
            asyncio.sleep(30)
