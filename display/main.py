import sys
import select
import time
from machine import WDT
from gfx_pack import GfxPack

# TODO: invert colors once a while to avoid lcd burn in?


# setup display
gp = GfxPack()
display = gp.display
WIDTH, HEIGHT = display.get_bounds()
display.set_backlight(0.5)  # turn off the white component of the backlight
display.set_font("bitmap8")

# enable the WDT with a timeout of 5s
wdt = WDT(timeout=5000)

MESSAGES = {
    "K": ("OK", "ACCESS GRANTED"),
    "Q": ("ERROR", "ERROR IN YOUR QR CODE"),
    "C": ("ERROR", "MEMBERSHIP CANCELED"),
    "F": ("ERROR", "COULD NOT FIND USER IN DB"),
    "D": ("ERROR", "YOUR DAYTICKET IS EXPIRED"),
    "U": ("ERROR", "COULD NOT UNPACK DATA IN QR CODE"),
    "S": ("ERROR", "WRONG SIGNATURE IN QR CODE"),
    ".": ("READY", "READY TO SCAN"),
    "E": ("ERROR", "SYSTEM ERROR"),
}


def show_message(header, text):
    display.set_pen(0)  # Set pen to white
    display.clear()
    display.set_pen(15)  # Set pen to black
    width = display.measure_text(header, scale=4)
    display.text(header, (WIDTH - width) // 2, 4, scale=4)
    width = display.measure_text(text, scale=1.5)
    display.text(text, (WIDTH - width) // 2, 44, scale=1.5)
    display.update()


if __name__ == "__main__":
    poll = select.poll()
    poll.register(sys.stdin, select.POLLIN)

    while True:
        # feed watchdog
        wdt.feed()
        if poll.poll(timeout=2000):
            data = sys.stdin.read(1)
            # print("#")  # print ACK back
            show_message(*MESSAGES.get(data))
            # sleep a little before next message
            if not data == ".":
                time.sleep(1.8)
        else:
            # system error
            show_message(*MESSAGES["E"])
