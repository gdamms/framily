# Framily Frame

This is the code that runs on the physical photo frame itself - a Raspberry Pi with an e-ink
display - as opposed to the server/web app in the rest of this repo. It drives the display and
handles connecting the frame to your Wi-Fi and to your Framily server.

## Hardware requirements

The frame was developed and tested on a [Raspberry PI Zero W](https://www.raspberrypi.com/products/raspberry-pi-zero-w/) (with headers) and a [Waveshare 7.3" e-Paper HAT (Spectra 6)](https://www.waveshare.com/product/raspberry-pi/displays/e-paper/7.3inch-e-paper-hat-e.html). Other Raspberry Pi models with the 40-pin GPIO header, Wi-Fi, and Bluetooth (needed for setup, see below) should work, but have not been tested. Other e-ink displays may work (especially Waveshare ones) but have not been tested and may require code changes.

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

A brand-new frame doesn't know your Wi-Fi yet, so it advertises itself over Bluetooth
(`Framily-XXXX`, shown on the display) and waits. Open the Framily mobile app, tap "Set up a
frame," and it'll find the frame, connect to it, and ask for your home Wi-Fi and your Framily
server's address. The frame joins that network, registers itself, and starts waiting for photos -
if it just created a new framily, the app joins it for you automatically and your first photo will
show up on the next fetch.

The frame's Bluetooth setup service runs continuously (it's a separate radio from Wi-Fi), so the
same app flow also works to reconfigure a frame that's already set up - e.g. after moving it to a
new router. There's also a browser-based fallback at the frame's LAN address (shown in the
framily's frame settings once it's online) for changing Wi-Fi/server settings or resetting the
frame without the app - but since it needs the frame to already have network, it can't be used for
first-time setup.
