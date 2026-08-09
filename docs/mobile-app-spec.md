# Mobile app: installable + seamless frame setup

Design notes for making the frontend installable on iOS/Android and adding a
"connect to a frame" flow that provisions a new frame without leaving the app.
Related to the existing TODO items "progressive web app" and "include frame
initialization in the pwa".

## Goal

From the mobile app, a user taps **"Connect to a frame"**, the app finds a
nearby unprovisioned frame, collects WiFi credentials with minimal typing,
sends them to the frame, and returns the user to the app once the frame is
online — including the brand-new-framily case (no separate "hotspot join"
step in the phone's WiFi settings).

## Required device capabilities

- Camera + gallery (picture upload — already core to the app)
- Push notifications
- Bluetooth (frame discovery + credential transfer)
- WiFi state (read the phone's currently-connected SSID)
- Installable on both iOS and Android from a single codebase

## Platform decision: Capacitor, not pure PWA, not Svelte Native

- **Svelte Native (NativeScript) is ruled out**: effectively unmaintained,
  and as far as known never updated for Svelte 5's runes/compiler output.
  The frontend is Svelte 5, so adopting it would mean forking a parallel
  codebase on old Svelte syntax.
- **A pure PWA can't cover the BLE requirement**: Web Bluetooth is
  unsupported in iOS Safari (Apple has never implemented it, no announced
  plans to). A PWA-only approach would work for Android but leave iOS with
  no discovery mechanism at all.
- **Capacitor** wraps the existing SvelteKit static build in a native shell
  and adds native plugins (BLE, camera, push, filesystem) per platform —
  reuses the current frontend almost as-is, and covers iOS + Android with
  one codebase. This is the recommended path.

## Feature compatibility summary

| Feature | PWA (iOS Safari) | PWA (Android Chrome) | Capacitor (iOS/Android) |
|---|---|---|---|
| Camera / gallery | Works (`<input capture>`) | Works | Works (native plugin) |
| Push notifications | Only if added to home screen, iOS 16.4+ | Works | Works (native plugin) |
| Bluetooth (BLE) | **Not supported** | Works (Web Bluetooth) | Works (native plugin, both) |
| Read saved WiFi password | Not possible (no such API exists anywhere) | Not possible | Not possible |
| Read currently-connected SSID | Not possible without native | Possible w/ location permission | Possible w/ location permission (both platforms) |
| Join a WiFi network programmatically | Not possible | Limited (`WifiNetworkSuggestion`) | `NEHotspotConfiguration` (iOS) / `WifiNetworkSuggestion` (Android) |

## Hard platform constraints (apply regardless of framework)

- **No app can read a WiFi password already saved on the phone**, on either
  OS. This is enforced by OS-level secure storage with no public API for
  third parties — not a framework limitation, so no implementation choice
  works around it.
- **Reading the currently-connected SSID requires location permission** on
  both iOS and Android (SSID can be used to infer location). Users will see
  a location-permission prompt as part of the flow — standard for this kind
  of app (same pattern used by smart-plug/IoT setup apps), but worth calling
  out in the UI copy so it doesn't read as suspicious.
- Net effect: the flow can auto-fill the network **name**, but must always
  ask the user to type the **password** once. "Fully zero-input" WiFi setup
  is not achievable on iOS or Android by any app.

## Proposed provisioning flow

1. User taps "Connect to a frame" in the app.
2. App starts a BLE scan (Capacitor BLE plugin) for frames advertising as
   unprovisioned.
3. On discovery, app reads the phone's current WiFi SSID (with location
   permission) and pre-fills it; user enters the password.
4. App writes SSID + password to the frame over a BLE GATT characteristic.
5. Frame (Pi) uses NetworkManager to join that network, then calls the
   existing `POST /framily/create` / `POST /framily/check` flow over HTTP
   once online, same as today.
6. App polls (or gets a BLE status characteristic update) confirming the
   frame is online and reachable, then transitions the user back into the
   main app / framily view.
7. If BLE isn't available (older phone, permission denied, discovery
   fails), fall back to the existing hotspot + local web UI flow
   (`frame/web/`) — keep it rather than replace it.

## Implied new work

- **Frontend**: migrate to Capacitor; add BLE, camera, and push notification
  plugins; handle location-permission prompt in the provisioning UI.
- **Frame (`frame/`)**: no Bluetooth code exists today. Needs a new BLE
  peripheral component (BlueZ GATT server) that advertises the frame and
  exposes characteristics for receiving SSID/password and reporting
  provisioning status. This runs alongside, not instead of, the existing
  NetworkManager/hotspot logic — `frame/agent/main.py` remains the sole
  owner of NetworkManager mutations.
- **Backend**: none of the existing framily/frame API surface changes —
  the frame still registers/checks via `FRAMILY_CREATE_PATH` /
  `FRAMILY_CHECK_PATH` once it has network access.

## Open questions

- Should the hotspot fallback stay permanently, or only as a
  reprovisioning path (e.g. after a factory reset)?
- Push notifications: what are they actually for (new picture uploaded?
  frame offline?) — affects whether iOS's home-screen-install requirement
  for push is a real constraint or a non-issue.
- BLE range/UX on a Pi: does the frame need a physical "pairing mode"
  button/timeout, or does it advertise indefinitely until provisioned?
