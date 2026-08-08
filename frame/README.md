# Framily Frame

This is the code that runs on the physical photo frame itself - a Raspberry Pi with an e-ink
display - as opposed to the server/web app in the rest of this repo. It drives the display and
handles connecting the frame to your Wi-Fi and to your Framily server.

## Hardware requirements

The frame was developed and tested on a [Raspberry PI Zero W](https://www.raspberrypi.com/products/raspberry-pi-zero-w/) (with headers) and a [Waveshare 7.3" e-Paper HAT (Spectra 6)](https://www.waveshare.com/product/raspberry-pi/displays/e-paper/7.3inch-e-paper-hat-e.htm). Other Raspberry Pi models with the 40-pin GPIO header and Wi-Fi should work, but have not been tested. Other e-ink displays may work (especially Waveshare ones) but have not been tested and may require code changes.

## Install

On a fresh Raspberry Pi, as root:

```sh
curl -sL https://raw.githubusercontent.com/gdamms/framily/main/frame/scripts/install.sh | sh
```

This installs everything the frame needs and starts it up. Re-running the same command later
upgrades an existing install in place, without losing its Wi-Fi setup or which framily it belongs
to.

By default this installs the latest tagged release. Pin to a specific version, or track nightly
builds, with `FRAMILY_VERSION`:

```sh
curl -sL .../install.sh | FRAMILY_VERSION=v1.0.0 sh   # pin to a release
curl -sL .../install.sh | FRAMILY_VERSION=nightly sh  # track main
```

## First boot

A brand-new frame doesn't know your Wi-Fi yet, so it starts its own hotspot (`Framily-XXXX`) and
shows a QR code on the display. Connect to that hotspot from a phone or laptop, open the page it
points to, and enter your home Wi-Fi and your Framily server's address. The frame reconnects,
registers itself, and starts waiting for photos - join the framily it created from the web app and
your first photo will show up on the next fetch.

If the frame ever loses its connection or its server for too long, it falls back to hotspot mode
automatically so you can reconfigure it the same way.
