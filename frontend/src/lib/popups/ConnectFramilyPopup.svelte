<script lang="ts">
  import Button from "$lib/ui/Button.svelte";
  import StatusMessage from "$lib/ui/StatusMessage.svelte";
  import { createStatusMessage } from "$lib/ui/statusMessage.svelte";
  import { api } from "$lib/api";

  interface Props {
    onSuccess?: () => void;
    close?: () => void;
  }

  let { onSuccess, close = () => {} }: Props = $props();

  let code = $state("");
  const status = createStatusMessage();

  async function handleConnect() {
    code = code.trim().toUpperCase();

    const codePattern = /^[A-Z0-9]{8}$/;
    if (!codePattern.test(code)) {
      status.show("Invalid code format. Code should be 8 alphanumeric characters.", "error");
      return;
    }

    status.show("Connecting...", "info", null);

    try {
      await api.framily.connect(code);
      status.show("Connected successfully!", "success");
      setTimeout(() => {
        onSuccess?.();
        close();
      }, 1000);
    } catch (error: any) {
      status.show(error?.response?.data?.message || "Failed to connect to framily", "error");
    }
  }
</script>

<div class="content">
  <StatusMessage text={status.text} type={status.type} />
  <h2>Connect to a Framily</h2>
  <p>Enter the Framily code for the first connection:</p>
  <input type="text" bind:value={code} placeholder="Framily code" />
  <div class="buttons">
    <Button variant="secondary" onclick={close}>Cancel</Button>
    <Button variant="primary" onclick={handleConnect}>Connect</Button>
  </div>
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
    gap: 20px;
  }

  .buttons {
    display: flex;
    gap: 10px;
  }
</style>
