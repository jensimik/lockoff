import sys
import select
import time
from machine import WDT
from gfx_pack import GfxPack


# setup display
gp = GfxPack()
display = gp.display
WIDTH, HEIGHT = display.get_bounds()
display.set_backlight(0.5)  # turn off the white component of the backlight
display.set_font("bitmap8")

# enable the WDT with a timeout of 5s
wdt = WDT(timeout=5000)

MESSAGES = {
    "K": ("OK", "ACCESS GRANTED", (0, 125, 0)),
    "Q": ("ERROR", "ERROR IN YOUR QR CODE", (125, 0, 0)),
    "C": ("ERROR", "MEMBERSHIP CANCELED", (125, 0, 0)),
    ".": ("READY", "READY TO SCAN", (125, 125, 125)),
    "E": ("ERROR", "SYSTEM ERROR", (255, 0, 0)),
}


def show_message(header, text, backlight):
    gp.set_backlight(backlight)
    display.set_pen(0)  # Set pen to white
    display.clear()
    display.set_pen(15)  # Set pen to black
    width = display.measure_text(header, scale=4)
    display.text(header, (WIDTH - width) // 2, 4, scale=4)
    width = display.measure_text(text, scale=2)
    display.text(text, (WIDTH - width) // 2, 44, scale=2)
    display.update()


if __name__ == "__main__":
    poll = select.poll()
    poll.register(sys.stdin, select.POLLIN)

    while True:
        # feed watchdog
        wdt.feed()
        if poll.poll(timeout=2000):
            data = sys.stdin.read(1)
            print("#")  # print ACK back
            show_message(**MESSAGES.get(data))
            # sleep a little before next message
            if not data == ".":
                time.sleep(1.8)
        else:
            # system error
            show_message(**MESSAGES["E"])
