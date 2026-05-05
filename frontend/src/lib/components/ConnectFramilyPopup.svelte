<script lang="ts">
  import Popup from "$lib/components/Popup.svelte";
  import Button from "$lib/components/Button.svelte";
  import { api } from "$lib/api/index";

  interface Props {
    isOpen?: boolean;
    onClose?: () => void;
  }

  let { isOpen = $bindable(false), onClose }: Props = $props();

  let code = $state("");

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
    code = code.trim().toUpperCase();

    // Verify code format (e.g., 8 alphanumeric characters)
    const codePattern = /^[A-Z0-9]{8}$/;
    if (!codePattern.test(code.trim())) {
      showMessage("Invalid code format. Code should be 8 alphanumeric characters.", "error");
      return;
    }

    showMessage("Connecting...", "info", null);

    try {
      await api.framily.connect(code);
      showMessage("Connected successfully!", "success");
      setTimeout(() => {
        onClose && onClose();
      }, 1000);
    } catch (error: any) {
      showMessage(
        error?.response?.data?.message || "Failed to connect to framily",
        "error",
      );
    }
  }

  async function close() {
    isOpen = false;
  }
</script>

<Popup bind:isOpen {onClose}>
  <div class="content">
    {#if message}
      <div class="message {messageType}">{message}</div>
    {/if}
    <h2>Connect to a Framily</h2>
    <p>Enter the Framily code for the first connection:</p>
    <input type="text" bind:value={code} placeholder="Framily code" />
    <div class="buttons">
      <Button onclick={close} color="#b8d9f2">Cancel</Button>
      <Button onclick={handleConnect}>Connect</Button>
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
