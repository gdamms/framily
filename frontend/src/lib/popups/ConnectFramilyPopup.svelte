<script lang="ts">
  import { m } from "$lib/i18n.svelte";
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
      status.show(m.connect_invalid_code(), "error");
      return;
    }

    status.show(m.common_connecting(), "info", null);

    try {
      await api.framily.connect(code);
      status.show(m.connect_success(), "success");
      setTimeout(() => {
        onSuccess?.();
        close();
      }, 1000);
    } catch (error: any) {
      status.show(error?.response?.data?.message || m.connect_failed(), "error");
    }
  }
</script>

<div class="content">
  <StatusMessage text={status.text} type={status.type} />
  <h2>{m.connect_title()}</h2>
  <p>{m.connect_prompt()}</p>
  <input type="text" bind:value={code} placeholder={m.connect_placeholder()} />
  <div class="buttons">
    <Button variant="secondary" onclick={close}>{m.common_cancel()}</Button>
    <Button variant="primary" onclick={handleConnect}>{m.connect_submit()}</Button>
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
