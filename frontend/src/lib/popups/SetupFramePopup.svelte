<script lang="ts">
  import { onDestroy, onMount } from "svelte";
  import Button from "$lib/ui/Button.svelte";
  import StatusMessage from "$lib/ui/StatusMessage.svelte";
  import { createStatusMessage } from "$lib/ui/statusMessage.svelte";
  import TextField from "$lib/ui/form/TextField.svelte";
  import PasswordField from "$lib/ui/form/PasswordField.svelte";
  import ServerUrlField from "$lib/ui/form/ServerUrlField.svelte";
  import { api } from "$lib/api";
  import { app } from "$lib/app";
  import { serverUrlStore } from "$lib/stores/serverUrl";
  import {
    scanForFrames,
    stopScan,
    connectToFrame,
    disconnectFromFrame,
    submitCredentials,
    watchProvisioningStatus,
    type DiscoveredFrame,
    type ProvisioningState,
  } from "$lib/ble/frameSetup";
  import Bluetooth from "@lucide/svelte/icons/bluetooth";
  import LoaderCircle from "@lucide/svelte/icons/loader-circle";

  interface Props {
    onSuccess?: () => void;
    close?: () => void;
  }

  let { onSuccess, close = () => {} }: Props = $props();

  type Phase = "scanning" | "connecting" | "credentials" | "submitting" | "waiting" | "error";

  let phase: Phase = $state("scanning");
  let frames: DiscoveredFrame[] = $state([]);
  let scanning = false;

  let connectedDeviceId: string | undefined = $state();
  let connectedName = $state("");

  let ssid = $state("");
  let password = $state("");
  let serverUrl = $state($serverUrlStore);

  let provisioning: ProvisioningState | undefined = $state();

  const status = createStatusMessage();

  const WAITING_LABELS: Record<string, string> = {
    idle: "Waiting for the frame...",
    connecting_wifi: "Connecting to Wi-Fi...",
    registering: "Checking the server...",
  };

  async function startScan() {
    phase = "scanning";
    frames = [];
    scanning = true;
    try {
      await scanForFrames((frame) => {
        frames = [...frames, frame];
      });
    } catch (e: any) {
      scanning = false;
      phase = "error";
      status.show(e?.message || "Bluetooth isn't available on this device.", "error", null);
    }
  }

  async function stopScanning() {
    if (!scanning) return;
    scanning = false;
    try {
      await stopScan();
    } catch {
      // Best-effort - nothing useful to do if this fails.
    }
  }

  async function selectFrame(frame: DiscoveredFrame) {
    await stopScanning();
    phase = "connecting";
    try {
      await connectToFrame(frame.deviceId, () => {
        if (phase === "credentials" || phase === "submitting" || phase === "waiting") {
          phase = "error";
          status.show("Lost connection to the frame.", "error", null);
        }
      });
      connectedDeviceId = frame.deviceId;
      connectedName = frame.name;
      phase = "credentials";
    } catch (e: any) {
      phase = "error";
      status.show(e?.message || "Could not connect to the frame.", "error", null);
    }
  }

  async function handleSubmit() {
    if (!connectedDeviceId) return;
    if (!ssid.trim() || !serverUrl.trim()) {
      status.show("Please fill in the Wi-Fi network and server URL.", "error");
      return;
    }

    phase = "submitting";
    try {
      await watchProvisioningStatus(connectedDeviceId, handleProvisioningUpdate);
      await submitCredentials(connectedDeviceId, ssid.trim(), password, serverUrl.trim());
      phase = "waiting";
    } catch (e: any) {
      phase = "error";
      status.show(e?.message || "Failed to send credentials to the frame.", "error", null);
    }
  }

  function handleProvisioningUpdate(state: ProvisioningState) {
    provisioning = state;

    if (state.status === "wifi_failed" || state.status === "server_failed") {
      // Let the user fix the fields and retry without rescanning/reconnecting.
      phase = "credentials";
      status.show(state.message || "Setup failed, please try again.", "error", null);
      return;
    }

    if (state.status === "success") {
      void finish(state);
    }
  }

  async function finish(state: ProvisioningState) {
    if (connectedDeviceId) {
      try {
        await disconnectFromFrame(connectedDeviceId);
      } catch {
        // Best-effort - the frame is provisioned either way.
      }
    }

    if (state.created_new_framily && state.framily_code) {
      try {
        await api.framily.connect(state.framily_code);
      } catch {
        // The frame already created the framily server-side - if joining it
        // here fails, it's not worth blocking the flow over.
      }
      onSuccess?.();
      close();
      app.navigate({ page: "framily", code: state.framily_code, section: "pictures" });
    } else {
      onSuccess?.();
      close();
    }
  }

  function rescan() {
    connectedDeviceId = undefined;
    provisioning = undefined;
    void startScan();
  }

  onMount(startScan);

  onDestroy(() => {
    void stopScanning();
  });
</script>

<div class="content">
  <StatusMessage text={status.text} type={status.type} />

  {#if phase === "scanning"}
    <h2>Set Up a Frame</h2>
    <p>Looking for nearby frames over Bluetooth...</p>
    <div class="frames">
      {#each frames as frame (frame.deviceId)}
        <button class="frame-item" onclick={() => selectFrame(frame)}>
          <Bluetooth size={18} />
          {frame.name}
        </button>
      {:else}
        <div class="scanning-placeholder">
          <LoaderCircle class="spin" size={20} />
          Scanning...
        </div>
      {/each}
    </div>
    <div class="buttons">
      <Button variant="secondary" onclick={close}>Cancel</Button>
    </div>
  {:else if phase === "connecting"}
    <h2>Connecting...</h2>
    <div class="scanning-placeholder">
      <LoaderCircle class="spin" size={20} />
      Connecting to the frame...
    </div>
    <div class="buttons">
      <Button variant="secondary" onclick={close}>Cancel</Button>
    </div>
  {:else if phase === "credentials" || phase === "submitting"}
    <h2>Connect {connectedName} to Wi-Fi</h2>
    <p>Enter your home Wi-Fi network and your Framily server's address.</p>
    <TextField placeholder="Wi-Fi SSID" bind:value={ssid} required />
    <PasswordField placeholder="Wi-Fi password" bind:value={password} />
    <ServerUrlField bind:value={serverUrl} />
    <div class="buttons">
      <Button variant="secondary" onclick={close} disabled={phase === "submitting"}>Cancel</Button>
      <Button variant="primary" onclick={handleSubmit} disabled={phase === "submitting"}>
        {phase === "submitting" ? "Sending..." : "Connect"}
      </Button>
    </div>
  {:else if phase === "waiting"}
    <h2>Setting Up Your Frame</h2>
    <div class="scanning-placeholder">
      <LoaderCircle class="spin" size={20} />
      {WAITING_LABELS[provisioning?.status ?? "idle"] ?? "Working..."}
    </div>
  {:else if phase === "error"}
    <h2>Setup Failed</h2>
    <div class="buttons">
      <Button variant="secondary" onclick={close}>Close</Button>
      <Button variant="primary" onclick={rescan}>Scan Again</Button>
    </div>
  {/if}
</div>

<style>
  .content {
    display: flex;
    flex-direction: column;
    align-items: center;
    background-color: var(--color-bg-surface-alt);
    color: var(--color-text);
    padding: 20px;
    border-radius: 10px;
    gap: 16px;
    width: min(90vw, 360px);
    box-sizing: border-box;
  }

  h2 {
    margin: 0;
  }

  p {
    margin: 0;
    text-align: center;
    color: var(--color-text-muted);
  }

  .frames {
    display: flex;
    flex-direction: column;
    gap: 8px;
    width: 100%;
    min-height: 3rem;
  }

  .frame-item {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.7rem 1rem;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    background: var(--color-bg-surface);
    color: var(--color-text);
    font: inherit;
    text-align: left;
    cursor: pointer;
  }

  .frame-item:hover {
    background-color: var(--color-bg-hover);
  }

  .scanning-placeholder {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.6rem;
    color: var(--color-text-muted);
    padding: 0.5rem 0;
  }

  :global(.spin) {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from {
      transform: rotate(0deg);
    }
    to {
      transform: rotate(360deg);
    }
  }

  .buttons {
    display: flex;
    gap: 10px;
  }
</style>
