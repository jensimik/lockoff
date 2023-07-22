import select
import sys
import time
from machine import RTC

from gfx_pack import SWITCH_A, GfxPack
from machine import WDT

# set clock to just 2000-01-01 00:00:00
rtc = RTC()
rtc.datetime((2000, 1, 1, 0, 0, 0, 0, 0))

# setup display
gp = GfxPack()
display = gp.display
WIDTH, HEIGHT = display.get_bounds()
display.set_backlight(0.2)  # turn off the white component of the backlight
display.set_font("bitmap8")


# small color helper
class Color:
    black = 15
    white = 0


color_schemes = {
    0: (Color.black, Color.white),
    1: (Color.white, Color.black),
}


MESSAGES = {
    ".": ("READY", "READY TO SCAN"),
    "K": ("OK", "ACCESS GRANTED"),
    "Q": ("ERROR", "ERROR IN YOUR QR CODE"),
    "C": ("ERROR", "MEMBERSHIP CANCELED"),
    "F": ("ERROR", "COULD NOT FIND USER IN DB"),
    "D": ("ERROR", "YOUR DAYTICKET IS EXPIRED"),
    "X": ("ERROR", "YOUR QR CODE IS EXPIRED"),
    "S": ("ERROR", "WRONG SIGNATURE IN QR CODE"),
    "E": ("ERROR", "SYSTEM ERROR"),
    "B": ("BOOT", "BOOT WAIT TIME"),
}


def get_color():
    _, _, _, hour, _, _, _, _ = rtc.datetime()
    return color_schemes[hour % 2]


def show_message(header, text):
    bg_color, text_color = get_color()
    display.set_pen(bg_color)  # Set pen to white
    display.clear()
    display.set_pen(text_color)  # Set pen to black
    width = display.measure_text(header, scale=4)
    display.text(header, (WIDTH - width) // 2, 4, scale=4)
    width = display.measure_text(text, scale=1.5)
    display.text(text, (WIDTH - width) // 2, 44, scale=1.5)
    display.update()


if __name__ == "__main__":
    # sleep for 10 seconds to allow for reprogramming
    if gp.switch_pressed(SWITCH_A):
        show_message(*MESSAGES["B"])
        time.sleep(10)

    # enable the WDT with a timeout of 8s (max)
    wdt = WDT(timeout=8000)

    # setup poll on stdin
    poll = select.poll()
    poll.register(sys.stdin, select.POLLIN)

    while True:
        # feed watchdog
        wdt.feed()
        if poll.poll(2000):
            data = sys.stdin.read(1)
            # print("#")  # print ACK back
            show_message(*MESSAGES.get(data, MESSAGES["E"]))
            # sleep a little before next message
            if not data == ".":
                time.sleep(1.8)
        else:
            # system error
            show_message(*MESSAGES["E"])
