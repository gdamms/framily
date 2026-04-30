<script lang="ts">
  import Popup from "$lib/components/Popup.svelte";
  import Button from "$lib/components/Button.svelte";
  import { api } from "$lib/api/index";

  interface Props {
    framilyCode: string;
    onClose?: () => void;
  }

  let { framilyCode, onClose }: Props = $props();

  let username = $state("");

  let message = $state();
  let messageType = $state<"info" | "error" | "success">();

  let messageTimeout: NodeJS.Timeout | null = null;

  async function showMessage(
    messageText: string,
    type: "info" | "error" | "success",
    timeout: number | null = 3000,
  ) {
    message = messageText;
    messageType = type;
    if (timeout) {
      clearTimeout(messageTimeout!);
      messageTimeout = setTimeout(() => {
        message = "";
        messageType = undefined;
      }, timeout);
    }
  }

  async function handleConnect() {
    username = username.trim();

    // Verify username format
    const usernamePattern = /^[a-zA-Z0-9_.-]{3,32}$/;
    if (!usernamePattern.test(username)) {
      showMessage("Invalid username format. Username should be between 3 and 32 characters.", "error");
      return;
    }

    showMessage("Connecting...", "info", null);

    try {
      await api.framily.invite(framilyCode,username);
      showMessage("Invitation sent successfully!", "success");
      setTimeout(() => {
        onClose && onClose();
      }, 1000);
    } catch (error: any) {
      showMessage(
        error?.response?.data?.message || "Failed to invite user to framily",
        "error",
      );
    }
  }
</script>

<Popup {onClose}>
  <div class="content">
    {#if message}
      <div class="message {messageType}">{message}</div>
    {/if}
    <h2>Invite to a Framily</h2>
    <p>Enter the username of the person you want to invite:</p>
    <input type="text" bind:value={username} placeholder="Username" />
    <div class="buttons">
      <Button onclick={onClose} color="#b8d9f2">Cancel</Button>
      <Button onclick={handleConnect}>Invite</Button>
    </div>
  </div>
</Popup>

<style>
  .content {
    display: flex;
    flex-direction: column;
    align-items: center;
    background-color: #f4fdff;
    padding: 20px;
    border-radius: 10px;
    gap: 20px;
  }

  .framilies {
    display: flex;
    flex-wrap: wrap;
    gap: 10px;
    justify-content: center;
  }

  .framily-checkbox {
    display: none;
  }

  .framily-label {
    padding: 10px 20px;
    background-color: #c8dadf;
    border-radius: 5px;
    cursor: pointer;
    transition: background-color 0.3s ease;
  }

  .message {
    padding: 10px 20px;
    border-radius: 5px;
    text-align: center;
    font-weight: bold;
  }

  .message.info {
    background-color: #c8dadf;
    color: #333;
  }
  .message.error {
    background-color: #e74c3c;
    color: white;
  }
  .message.success {
    background-color: #2ecc71;
    color: white;
  }

  .buttons {
    display: flex;
    gap: 10px;
  }
</style>
