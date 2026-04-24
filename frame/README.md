# Framily Frame

## Setup

Use the setup suite entrypoint to provision or upgrade a frame in an idempotent way:

```sh
cd /home/framily/frame
sudo sh setup/full_setup.sh
```

Compatibility wrappers still exist:

- `setup.sh` calls `setup/full_setup.sh`
- `setup_net.sh` calls `setup/40_network.sh`
- `epd/setup.sh` and `framily_flask/setup.sh` call `setup/50_services.sh`

### Setup suite steps

1. `setup/10_preflight.sh`: root/system checks, service user and base directories.
2. `setup/20_dependencies.sh`: system and Python dependencies.
3. `setup/30_deploy_files.sh`: deploy frame files and initialize config files.
4. `setup/40_network.sh`: idempotent NetworkManager profile + dispatcher + dns config.
5. `setup/50_services.sh`: install and restart services.
6. `setup/60_verify.sh`: verify core services and expected profiles.

## Runtime behavior

1. On hotspot mode, the frame generates new credentials each time in the format:
   - SSID: `Framily-XXXX`
   - Password: `XXXXXXXX`
2. The setup page shows current state and last error details.
3. After setup, runtime flow is:
   - connect Wi-Fi
   - create framily if not already registered
   - wait until framily has at least one member
   - fetch pictures every 60 seconds
4. If no picture is available, the frame displays the first-image placeholder.
5. Transient failures are retried with backoff. Persistent failures switch to hotspot mode.

## Deploy helper

`send.sh` supports optional target and optional remote setup:

```sh
cd /home/framily/frame
sh send.sh framily@10.42.0.1

# Optional remote setup run
RUN_SETUP=1 sh send.sh framily@10.42.0.1
```

## Notes

- The setup suite is designed for both fresh setup and upgrades.
- Network profile setup is Framily-scoped and does not delete unrelated Wi-Fi profiles.
