<script lang="ts">
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
      status.show("Invalid username format. Username should be between 3 and 32 characters.", "error");
      return;
    }

    status.show("Connecting...", "info", null);

    try {
      await api.framily.invite(framilyCode, username);
      status.show("Invitation sent successfully!", "success");
      setTimeout(() => {
        onSuccess?.();
        close();
      }, 1000);
    } catch (error: any) {
      status.show(error?.response?.data?.message || "Failed to invite user to framily", "error");
    }
  }
</script>

<div class="content">
  <StatusMessage text={status.text} type={status.type} />
  <h2>Invite to a Framily</h2>
  <p>Enter the username of the person you want to invite:</p>
  <input type="text" bind:value={username} placeholder="Username" />
  <div class="buttons">
    <Button variant="secondary" onclick={close}>Cancel</Button>
    <Button variant="primary" onclick={handleInvite}>Invite</Button>
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
