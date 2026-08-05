# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

Framily is a self-hosted digital photo frame system. Family members upload photos through a web
app to a shared gallery; a physical e-ink frame device (Raspberry Pi) polls the backend and
displays them. The repo has three independently deployable components plus shared compose/env
config:

- `backend/` — FastAPI + SQLAlchemy + Postgres + S3-compatible storage (Garage). Serves the API
  and, in production, the built frontend static files.
- `frontend/` — SvelteKit (Svelte 5) SPA, built statically and served by the backend in prod.
- `frame/` — Python code that runs *on the physical Raspberry Pi frame*, not in Docker: e-ink
  display driver, Wi-Fi/hotspot provisioning, and a local setup web UI.
- `config/` — shared `docker-compose.dev.yml` / `docker-compose.prod.yml` and env file templates
  used by both dev and prod stacks.

## Development workflow (backend + frontend, via Docker Compose)

All commands run from the repo root via the `Makefile`, which wraps `docker-compose` with the
files in `config/compose/` and `config/env/`.

```sh
make setup       # one-time: copies config/env/dev.env.example -> config/env/.env, adds UID/GID
make start       # docker-compose up (dev stack: postgres, garage, backend, frontend)
make startd      # same, detached
make stop        # docker-compose down
make restart     # docker-compose restart
make clean       # down --rmi all --volumes --remove-orphans (destructive, prompts for confirmation)

make start-prod  # prod stack, needs config/env/.env.prod
make start-prodd
make stop-prod
```

Dev stack service ports/vars come from `config/env/dev.env.example` (copied to `.env` by
`make setup` / `scripts/setup.sh`). The frontend dev container runs `vite dev` with hot reload;
the backend dev container runs `entrypoint.dev.sh`, which does `uv sync --frozen`, then
`alembic upgrade head`, then `uvicorn main:app --reload`. Both mount the source tree as a bind
volume, so no rebuild is needed for code changes — only for dependency changes.

Storage backend is [Garage](https://garagehq.deuxfleurs.fr/) (an S3-compatible object store),
configured via `config/garage/garage.toml`; the backend talks to it through `boto3`
(`backend/core/minio.py`, despite the filename).

### Backend (FastAPI), outside Docker

```sh
cd backend
uv sync                        # install deps (uv is the package manager; see uv.lock)
uv run alembic upgrade head    # apply migrations
uv run uvicorn main:app --reload --port 8000
```

Migrations live in `backend/migrations/versions/`, numbered sequentially
(`0001_create_users.py`, ...). Generate a new one with:

```sh
uv run alembic revision -m "description"          # hand-written
uv run alembic revision --autogenerate -m "..."    # diff against models/
```

There is currently no automated test suite for the backend or frontend — don't assume `pytest`
or `npm test` exist.

### Frontend (SvelteKit), outside Docker

```sh
cd frontend
npm install
npm run dev       # vite dev server
npm run build     # static build (adapter-static, SPA fallback to index.html)
npm run preview   # preview the production build
npm run check     # svelte-kit sync && svelte-check (type checking)
```

The frontend is built as a static SPA (`adapter-static`, `fallback: 'index.html'`). In production
the backend serves it directly: `backend/main.py` has a catch-all route that serves
`FRONTEND_DIST_DIR` (default `/app/frontend-build`) for any non-`/api/` path, falling back to
`index.html` for client-side routing.

### Frame device code

`frame/` is deployed to and run on the Raspberry Pi itself, not containerized. Setup on the
device is driven by `frame/scripts/setup.sh`, which runs numbered steps in order:
`10_preflight.sh` (root/user/dir checks) → `20_dependencies.sh` → `30_deploy_files.sh` →
`40_network.sh` (NetworkManager profile + dispatcher + dnsmasq config) → `50_start.sh` (installs
and starts the systemd services). `frame/README.md` describes a more elaborate `setup/` suite
with additional wrappers and a verify step — treat that file as aspirational/partially stale and
check `frame/scripts/` for what's actually present before relying on step names from the README.

## Backend architecture

- `backend/main.py` — FastAPI app entrypoint. Configures CORS from `settings.CORS_ORIGINS`,
  mounts the versioned API router, and (if `SERVE_FRONTEND=true`) adds the static-frontend
  catch-all route.
- `backend/api/__init__.py` — aggregates all `api/v1/*` routers under prefix `/api/v1`.
  `backend/api/v1/`: `health.py`, `auth.py`, `framily.py`, `pictures.py`, `user.py`. Adding a new
  resource means creating a router module here and registering it in `api/__init__.py`.
- `backend/core/config.py` — single `Settings` (pydantic-settings) object read from `.env` /
  process env, imported everywhere as `from core.config import settings`. Has a
  `model_validator` that hard-fails at startup in production if `SECRET_KEY` or `CORS_ORIGINS`
  are left at insecure defaults.
- `backend/core/database.py` — SQLAlchemy engine/session; `get_db()` is the FastAPI dependency
  used by every route needing DB access.
- `backend/core/security.py` — password hashing (`passlib`/bcrypt) and JWT creation
  (`python-jose`).
- `backend/core/minio.py` — lazily-initialized `boto3` S3 client wrapper (`s3_client` proxy
  object) pointed at Garage; auto-creates the bucket if missing. All picture/profile-picture
  bytes live here under `S3_BUCKET`, not in Postgres.
- `backend/models/` — SQLAlchemy ORM models: `User`, `Framily`, `FramilySettings`, `Membership`,
  `Picture`, `PictureVisibility`. `backend/schemas/` — Pydantic request/response models, one file
  per resource, mirroring `models/`.

### Auth

`api/v1/auth.py` defines `get_current_user`, the dependency used across all protected routes. It
reads the JWT from an `auth_token` cookie first, falling back to a `Bearer` header
(`HTTPBearer(auto_error=False)`). Tokens are opaque JWTs with `sub` = user id, signed with
`SECRET_KEY`/`ALGORITHM`, expiring after `ACCESS_TOKEN_EXPIRE_MINUTES`. There's no refresh-token
flow — the frontend just re-logs-in on 401 (see `frontend/src/lib/api/client.ts`).

### Domain model — framilies, membership, visibility

A **framily** is the sharing unit a physical frame is bound to (`Framily.frame_token`,
`Framily.code` — an 8-char public join code). `Membership.role` is an int: `0` = invited
(pending), `1` = member, `2` = admin. Helper predicates `is_member`/`is_admin` in
`api/v1/framily.py` are imported by `pictures.py` and `user.py` — this is the shared
authorization primitive across the API, not a separate permissions module.

Pictures are decoupled from framilies via the `PictureVisibility` join table (many-to-many): a
single uploaded picture can be visible to multiple framilies, and visibility can be added/removed
independently of deleting the picture (`POST /pictures/add-visibility`,
`POST /pictures/remove-visibility` vs. `DELETE /pictures/{id}`, which only the uploader can do).
A framily admin can remove visibility for their framily (moderation) even if they didn't upload
the picture, but cannot delete someone else's picture outright.

Two endpoints are frame-device-only and authenticate via `framily_code` + `frame_token` in the
request body instead of user JWT: `POST /framily/create`, `POST /framily/check`, and
`POST /pictures/fetch` (returns a random visible picture as a streamed image, or 204 if none).

## Frontend architecture

SvelteKit is used mostly as a build tool/SPA shell here, not for its file-based routing: real
SvelteKit routes only exist for `/login` and `/register` (`frontend/src/routes/`). The main
authenticated app is a **single route** (`+page.svelte`) that switches views itself via an
in-memory store, `frontend/src/lib/app.ts` (`app.state` / `app.navigate(page)`), with a
discriminated-union `Page` type (`dashboard | framilies | profile | framily | picture`). When
adding a new "screen," it usually means adding a variant to `Page` and a case in the main page's
render logic rather than adding a SvelteKit route.

- `frontend/src/lib/api/client.ts` — the shared `fetch` wrapper (`request`, `requestFormData`,
  `requestBlob`). Always sends `credentials: "include"` (the JWT lives in the `auth_token`
  cookie, set by `frontend/src/lib/stores/auth.ts`, not localStorage). On a 401 it clears auth
  state and redirects to `/login` exactly once (`isRedirectingToLogin` guard).
- `frontend/src/lib/api/{auth,user,framily,pictures}.ts` — one module per backend resource,
  re-exported through `frontend/src/lib/api/index.ts` as the `api` object
  (`api.auth`, `api.user`, `api.framily`, `api.pictures`) plus individual named exports.
- `frontend/src/lib/stores/auth.ts` — reads/writes the `auth_token` cookie directly (not an
  httpOnly cookie set by the backend); this is the source of truth for `isAuthenticated`.
- `API_BASE_URL` defaults to `/api/v1` (relative, works when backend serves the frontend) but can
  be overridden with `VITE_API_URL` for split dev containers.

## Frame device architecture

Everything under `frame/` runs directly on the Raspberry Pi's OS (systemd services), independent
of the Docker Compose stack. The code stays flat and pragmatic — there was previously a layered
`frame_core/` shared library, but it was deliberately removed; don't reintroduce that pattern.

- `frame/utils.py` — shared helpers imported by every component: env-var-backed constants
  (`FRAMILY_*`), `run()` (subprocess wrapper around `nmcli`, with a timeout so a hung call can't
  wedge a caller), Wi-Fi/hotspot get/set helpers, `load_config()`/`save_config()` for the
  persisted `config.json` (server URL, framily registration, and the pending-Wi-Fi-intent fields
  the web UI writes for the agent to pick up), `AGENT_LOCK_PATH`/`AGENT_RECHECK_PATH`.
- `frame/logging_setup.py` — one `get_logger(name)` helper used by every component instead of
  `print()`: logs to `journald` and to a size-capped rotating file at `FRAMILY_LOG_PATH`
  (default `/opt/framily/framily.log`), which the web UI exposes at `/logs`.
- `frame/agent/main.py` (`framily-agent.service`, `Restart=always`) — the actual brain: decides
  Wi-Fi vs. hotspot mode by polling NetworkManager state itself (not dependent on the dispatcher
  hook firing), registers/checks the framily, and polls `PICTURE_FETCH_PATH` on the
  server-configured interval (clamped to a sane range). Transient failures (5xx, network errors)
  retry with backoff (`FrameApiError(transient=True)`, a handful of consecutive attempts) before
  falling back to hotspot mode. It's the sole owner of NetworkManager mutations — nothing else
  calls `nmcli` to change connections — and holds an `fcntl` lock (`AGENT_LOCK_PATH`) so only one
  instance runs at a time.
- `frame/epd/` — the e-ink panel driver (`epd7in3e.py`, vendor-derived) plus `main.py`
  (`framily-epd.service`), which watches the image file's parent directory (not the file itself —
  more robust against the file not existing yet or watchdog/inotify edge cases) and redraws on
  change.
- `frame/web/` — the local setup UI (`framily-web.service`, `Restart=always`, threaded Flask dev
  server), reachable at whatever address the frame currently has (Wi-Fi LAN IP or hotspot IP) in
  either mode. `/setup` only writes the requested Wi-Fi/server intent into `config.json` — it does
  not call `nmcli` directly, so a stuck `nmcli` can never wedge the UI. `/logs` serves the tail of
  the shared log file.
- `frame/dispatcher/framily.py` — a NetworkManager dispatcher hook, deliberately thin: on a
  `wlan0` state change it just touches `AGENT_RECHECK_PATH` so the agent reacts faster than its
  own poll interval. It holds no logic of its own and is never required for correctness — the
  agent doesn't depend on it firing.

Runtime flow (see `frame/README.md` for more detail): the agent connects to Wi-Fi → calls
`FRAMILY_CREATE_PATH` to register if not already registered → polls `FRAMILY_CHECK_PATH` until the
framily has ≥1 member → polls `PICTURE_FETCH_PATH` on the configured interval. Persistent failures
fall back to hotspot mode so the device can be reprovisioned. If hotspot mode, credentials are
regenerated each time (`Framily-XXXX` SSID).

## Conventions worth knowing

- Backend uses `uv` (not pip/poetry) — always `uv sync` / `uv run ...`, respect `uv.lock`.
- `role` is a plain `int` (0/1/2) in the DB and API today, not an enum — see `TODO.md`, this is
  a known planned change, don't assume an enum exists.
- The S3 wrapper module is named `core/minio.py` for historical reasons but talks to Garage via
  `boto3`, not the `minio` Python client — don't be misled by the filename or the leftover
  `minio` dependency in `pyproject.toml`.
- `config/env/*.env.example` are templates; the real `.env` (dev) / `.env.prod` (prod) are
  git-ignored and generated by `scripts/setup.sh` / `make setup`.
