# Framily Frame

This is the code that runs on the physical photo frame itself - a Raspberry Pi with an e-ink
display - as opposed to the server/web app in the rest of this repo. It drives the display and
handles connecting the frame to your Wi-Fi and to your Framily server.

## Requirements

- A Raspberry Pi (any model with the 40-pin GPIO header) running Raspberry Pi OS (Bookworm or
  newer), with an SD card and Wi-Fi.
- A [Waveshare 7.3" e-Paper HAT (Spectra 6)](https://www.waveshare.com/product/raspberry-pi/displays/e-paper.htm),
  attached to the Pi's GPIO header.
- A running Framily server (see the [root README](../README.md)) reachable from the frame's Wi-Fi
  network.

## Install

On a fresh Raspberry Pi, as root:

```sh
curl -sL https://raw.githubusercontent.com/gdamms/framily/main/frame/scripts/install.sh | sh
```

This installs everything the frame needs and starts it up. Re-running the same command later
upgrades an existing install in place, without losing its Wi-Fi setup or which framily it belongs
to.

## First boot

A brand-new frame doesn't know your Wi-Fi yet, so it starts its own hotspot (`Framily-XXXX`) and
shows a QR code on the display. Connect to that hotspot from a phone or laptop, open the page it
points to, and enter your home Wi-Fi and your Framily server's address. The frame reconnects,
registers itself, and starts waiting for photos - join the framily it created from the web app and
your first photo will show up on the next fetch.

If the frame ever loses its connection or its server for too long, it falls back to hotspot mode
automatically so you can reconfigure it the same way.
