# Lockoff - a single door access system

_Lock-off (n): the act of pulling on a hold until your arm is in a bent position, then holding that position using body tension in order to reach the next hold with your free hand._

Components:

- Sync of member data from [Klubmodul](https://klubmodul.dk)
- [Opticon USB barcode scanner](https://opticon.shop/scanners/stationary/opticon-m-11-usb/)
- [Pimoroni Badger 2040 w display](https://shop.pimoroni.com/products/badger-2040-w?variant=40514062188627)
- [Edatec CM4 nano / raspberry pi](https://www.edatec.cn/en/elpc/cm4-nano.html) ([manual](https://docs.edatec.cn/cm4-nano/))
- [Pimoroni Automation hat mini](https://shop.pimoroni.com/products/automation-hat-mini) ([manual](https://github.com/pimoroni/automation-hat))
- 12/24 volt door deadbolt
- iBeacon on the Badger/[iBeacon micropython](https://gist.github.com/N3MIS15/589062360a658a36b9c810fec8bb0c91)
- _Signed_ QR codes for access (Apple/Android wallet or printed)

[![Lockoff-Testing](https://github.com/jensimik/lockoff/actions/workflows/backend.yml/badge.svg)](https://github.com/jensimik/lockoff/actions/workflows/backend.yml) [![CodeQL](https://github.com/jensimik/lockoff/actions/workflows/github-code-scanning/codeql/badge.svg)](https://github.com/jensimik/lockoff/actions/workflows/github-code-scanning/codeql)
