# Framily Frame

Code that runs directly on the physical e-ink frame (Raspberry Pi), outside Docker: the
e-ink display loop, the NetworkManager dispatcher hook that drives Wi-Fi/hotspot transitions,
and a small local setup web UI.

## Install

On a fresh Raspberry Pi, as root:

```sh
curl -sL https://raw.githubusercontent.com/gdamms/framily/main/frame/scripts/install.sh | sh
```

This downloads the latest `framily.tar.gz` from `main`, extracts it to `/opt/framily`, and runs
the setup steps (dependencies, file deployment, network profiles, services).

Re-running the same command later upgrades an existing install in place: everything under
`/opt/framily` is replaced except `config.env` and `config.json`, which hold the frame's live
Wi-Fi/hotspot state and its framily registration — those are preserved across upgrades.
Network setup is also idempotent: it only creates the Framily Wi-Fi/hotspot NetworkManager
connections if they don't already exist, so a reinstall never wipes a working frame back to
unprovisioned.

## Local / dev install

To iterate on frame code without cutting a new tarball on `main`, copy `scripts/install.sh` and
a locally-built `framily.tar.gz` into the same folder on the frame and run it there:

```sh
scp framily.tar.gz scripts/install.sh framily@<frame-ip>:~
ssh framily@<frame-ip> 'sudo sh install.sh'
```

`install.sh` looks for `framily.tar.gz` in the current directory first; if it finds one, it uses
it as-is and never touches the network. If not found, it downloads it from `main` instead, then
deletes the downloaded copy once install succeeds — so nothing is left behind that you didn't
put there yourself.

## Rebuilding the tarball

`scripts/archive.sh` builds `framily.tar.gz` from the current contents of `frame/`, excluding
`.git`, `__pycache__`, `*.pyc`, the local `tmp/` scratch folder, and any runtime `config.json`:

```sh
sh frame/scripts/archive.sh
git add frame/framily.tar.gz
git commit -m "..."
```

There's no CI step for this — run it yourself and commit the result whenever you want `main`'s
tarball to reflect a source change. Anything you drop in `frame/tmp/` is gitignored local scratch
(e.g. saved API responses, throwaway test scripts) and never ends up in the archive.

## What setup does

`install.sh` extracts the tarball, then runs `scripts/setup.sh`, which runs these in order:

1. `10_preflight.sh` — root check, requires `systemd`.
2. `20_dependencies.sh` — system and Python dependencies, enables SPI.
3. `30_deploy_files.sh` — installs the systemd units, the NetworkManager dispatcher hook, and
   sets permissions. App code itself isn't copied elsewhere — it runs in place from
   `/opt/framily` (`WorkingDirectory=/opt/framily` in both services).
4. `40_network.sh` — creates the Framily Wi-Fi and hotspot NetworkManager connections if they
   don't already exist.
5. `50_start.sh` — enables and (re)starts `framily-epd.service` and `framily-web.service`,
   restarts NetworkManager.

## Runtime behavior

1. The frame connects using the `framily-wifi` NetworkManager connection if configured,
   otherwise falls back to the `framily-hotspot` connection (SSID/password come from
   `config.env`'s `FRAMILY_HOTSPOT_SSID`/`FRAMILY_HOTSPOT_PASSWORD`).
2. In hotspot mode, the display shows a Wi-Fi QR code and the local setup web UI's URL/QR code.
   The setup UI lets you point the frame at a server and Wi-Fi network.
3. Once on Wi-Fi with a server URL configured, the frame registers a framily (if not already
   registered) via `POST /api/v1/framily/create`, storing `framily_code`/`frame_token` in
   `config.json`, then polls `POST /api/v1/framily/check` every 5s until the framily has at
   least one member.
4. It then polls `POST /api/v1/pictures/fetch` every 60s and renders whatever picture comes
   back. A `204` response (no picture yet) shows a "waiting for first image" placeholder
   instead.
5. Any request failure (network error or non-OK response) shows an error message on the setup
   UI and switches the frame back to hotspot mode so it can be reprovisioned.

## Notes

- `/opt/framily` is hardcoded across `config.env`, both systemd units, and the dispatcher
  script — there's currently no supported way to install elsewhere.
- Frame device code (this directory) is independent of the Docker Compose stack used for
  `backend/`/`frontend/` development.
