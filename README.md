# Lockoff - a door access system

_Lock-off (n): the act of pulling on a hold until your arm is in a bent position, then holding that position using body tension in order to reach the next hold with your free hand._

Controller:

- Sync of member data from [Klubmodul](https://klubmodul.dk)
- [Opticon USB barcode scanner](https://opticon.shop/scanners/stationary/opticon-m-11-usb/)
- [Edatec CM4 nano / raspberry pi](https://www.edatec.cn/en/elpc/cm4-nano.html) ([manual](https://docs.edatec.cn/cm4-nano/))
- [Pimoroni Automation hat mini](https://shop.pimoroni.com/products/automation-hat-mini) ([manual](https://github.com/pimoroni/automation-hat))
- 12/24 volt door deadbolt
- ibeacon using bluetooth on the raspberry
- _Signed_ QR codes for access (Apple/Android wallet with geo+ibeacon or pdf-printed pass)

Display:

- [Raspberry Pico W](https://shop.pimoroni.com/products/raspberry-pi-pico-w?variant=40454061752403)
- [Pico GFX pack](https://shop.pimoroni.com/products/pico-gfx-pack?variant=40414469062739)
- Show status messages from the controller (connected and powered with USB)

![lockoff1](https://github.com/user-attachments/assets/674ae202-a883-4bad-ba9a-e3ef5b5fd088)


https://github.com/user-attachments/assets/c801137b-c7ea-4c59-a9cf-34055e9e2a4f



[![backend](https://github.com/jensimik/lockoff/actions/workflows/backend.yml/badge.svg)](https://github.com/jensimik/lockoff/actions/workflows/backend.yml) [![reader](https://github.com/jensimik/lockoff/actions/workflows/reader.yml/badge.svg)](https://github.com/jensimik/lockoff/actions/workflows/reader.yml) [![frontend](https://github.com/jensimik/lockoff/actions/workflows/frontend.yml/badge.svg)](https://github.com/jensimik/lockoff/actions/workflows/frontend.yml) [![cov-backend](https://codecov.io/gh/jensimik/lockoff/branch/main/graph/badge.svg?token=6ZCJSY0L7K&flag=backend)](https://codecov.io/gh/jensimik/lockoff) [![cov-reader](https://codecov.io/gh/jensimik/lockoff/branch/main/graph/badge.svg?token=6ZCJSY0L7K&flag=reader)](https://codecov.io/gh/jensimik/lockoff) [![cov-frontend](https://codecov.io/gh/jensimik/lockoff/branch/main/graph/badge.svg?token=6ZCJSY0L7K&flag=frontend)](https://codecov.io/gh/jensimik/lockoff)
