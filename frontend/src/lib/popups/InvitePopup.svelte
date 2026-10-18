<script lang="ts">
  import { m } from "$lib/i18n.svelte";
  import Button from "$lib/ui/Button.svelte";
  import StatusMessage from "$lib/ui/StatusMessage.svelte";
  import { createStatusMessage } from "$lib/ui/statusMessage.svelte";
  import { api } from "$lib/api";

  interface Props {
    framilyCode: string;
    onSuccess?: () => void;
    close?: () => void;
  }

  let { framilyCode, onSuccess, close = () => {} }: Props = $props();

  let username = $state("");
  const status = createStatusMessage();

  async function handleInvite() {
    username = username.trim();

    const usernamePattern = /^[a-zA-Z0-9_.-]{3,32}$/;
    if (!usernamePattern.test(username)) {
      status.show(m.invite_invalid_username(), "error");
      return;
    }

    status.show(m.common_connecting(), "info", null);

    try {
      await api.framily.invite(framilyCode, username);
      status.show(m.invite_success(), "success");
      setTimeout(() => {
        onSuccess?.();
        close();
      }, 1000);
    } catch (error: any) {
      status.show(error?.response?.data?.message || m.invite_failed(), "error");
    }
  }
</script>

<div class="content">
  <StatusMessage text={status.text} type={status.type} />
  <h2>{m.invite_title()}</h2>
  <p>{m.invite_prompt()}</p>
  <input type="text" bind:value={username} placeholder={m.invite_placeholder()} />
  <div class="buttons">
    <Button variant="secondary" onclick={close}>{m.common_cancel()}</Button>
    <Button variant="primary" onclick={handleInvite}>{m.invite_submit()}</Button>
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
