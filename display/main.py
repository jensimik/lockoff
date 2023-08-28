import select
import sys
import time

from gfx_pack import SWITCH_A, GfxPack
from machine import WDT

# setup display
gp = GfxPack()
display = gp.display
WIDTH, HEIGHT = display.get_bounds()
display.set_backlight(0.2)  # dim backlight
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
    ",": ("READY", "READY TO SCAN", 0),
    ".": ("READY", "READY TO SCAN", 1),
    "K": ("OK", "ACCESS GRANTED", 1),
    "J": ("ELJEFE", "ELJEFE IN DA HOUSE", 1),
    "M": ("ERROR", "MORNING OUTSIDE HOURS", 1),
    "Q": ("ERROR", "ERROR IN YOUR QR CODE", 1),
    "C": ("ERROR", "MEMBERSHIP CANCELED", 1),
    "F": ("ERROR", "COULD NOT FIND USER IN DB", 1),
    "D": ("ERROR", "YOUR DAYTICKET IS EXPIRED", 1),
    "X": ("ERROR", "YOUR QR CODE IS EXPIRED", 1),
    "S": ("ERROR", "WRONG SIGNATURE IN QR CODE", 1),
    "E": ("ERROR", "SYSTEM ERROR", 1),
    "B": ("BOOT", "BOOT WAIT TIME", 1),
}


def show_message(header, text, color_scheme):
    bg_color, text_color = color_schemes[color_scheme]
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

    # start tick and show ready message
    tick1 = time.ticks_ms()
    show_message(*MESSAGES["."])
    # main loop
    while True:
        # feed watchdog
        wdt.feed()
        if poll.poll(2000):
            data = sys.stdin.read(1)
            if data in [".", ","]:
                if time.ticks_diff(time.ticks_ms(), tick1) > 5000:
                    show_message(*MESSAGES.get(data, MESSAGES["E"]))
            else:
                show_message(*MESSAGES.get(data, MESSAGES["E"]))
                tick1 = time.ticks_ms()
        else:
            # system error
            show_message(*MESSAGES["E"])
