# Framily

A self-hosted digital photo frame system that connects families together. Family members upload
photos through a web app to a shared gallery, and a physical e-ink frame device polls the server
and displays them at home - no cloud service, no subscription, your photos stay on your own
server.

## Features

- **Framilies** - a "framily" is a shared photo circle bound to one physical frame. 
- **Captions**, per-picture, shown on the frame alongside the uploader's name and date.
- **E-ink tuned display** - pictures are automatically preprocessed (contrast/brightness) for the
  frame's 6-color Spectra e-paper panel, with an adjustable preprocessing intensity.
- **Configurable frame behavior** - display interval and orientation are set from the web app and
  picked up by the frame on its next fetch.
- **Zero-touch Wi-Fi provisioning** - a brand-new frame boots into its own hotspot with a QR code;
  connect once from a phone to hand it your Wi-Fi and server address.

## How it works

Framily is three independently deployable pieces:

- **`backend/`** - a FastAPI + Postgres + S3-compatible storage (Garage) API. In production it
  also serves the built frontend, so most deployments are a single service.
- **`frontend/`** - a SvelteKit SPA: the web app family members use to upload and browse photos.
- **`frame/`** - Python code that runs directly on the Raspberry Pi frame itself (not in Docker):
  the e-ink display driver and Wi-Fi provisioning. See [frame/README.md](frame/README.md).

## Requirements

- **Server**: to run the backend (and frontend). It is recommended to use docker-compose.
- **Frame**: a Raspberry Pi with a Waveshare 7.3" e-Paper (Spectra 6) HAT. See
  [frame/README.md](frame/README.md) for details. (This is the only hardware supported at the moment, but other e-ink panels could be added in the future.)

## Try it

The fastest way to see Framily running is the demo stack, which pulls the published image from
GHCR instead of building anything:

```sh
git clone https://github.com/gdamms/framily.git
cd framily
cp config/env/demo.env config/env/.env.demo   # then fill in real secrets
make start-demod
```

Open `http://localhost:8000`.

## Self-hosting (production)

For a real deployment, use the production stack - either build the image from source or point it
at a specific published release by setting `VERSION` in your env file:

```sh
cp config/env/prod.env config/env/.env.prod   # fill in real secrets and CORS_ORIGINS
make start-prodd
```

See the comments in `config/env/prod.env` for what each variable does, and
[frame/README.md](frame/README.md) to pair a physical frame with the framily it creates.

## Setting up the frame

On a fresh Raspberry Pi, as root:

```sh
curl -sL https://raw.githubusercontent.com/gdamms/framily/main/frame/scripts/install.sh | sh
```

Full details, requirements, and how to point the frame at your server are in
[frame/README.md](frame/README.md).

## Development

Contributors: `make setup && make start` brings up the dev stack (Postgres, Garage, backend with
hot reload, frontend with hot reload). `CLAUDE.md` has the full architecture and workflow
reference for the codebase.

There's currently no automated test suite for the backend or frontend - verify changes by running
the dev stack and exercising the feature by hand.

## Contributing

Issues and pull requests are welcome. `TODO.md` tracks planned work if you're looking for
something to pick up (it is written as it comes out of my mind so... good luck).

## License

AGPL-3.0 - Copyright (C) 2025 Damien Guillotin. See [LICENSE](LICENSE).

If your Framily server is reachable over a network, the AGPL requires that anyone interacting with
it be able to get the source of the exact version running there (including your own
modifications) - a link to this repository, or your fork if you've changed it, satisfies this.
