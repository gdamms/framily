<script lang="ts">
  import type { FramilyInfo } from "$lib/api";
  import Popup from "$lib/components/Popup.svelte";
  import UploadZone from "$lib/components/UploadZone.svelte";
  import Button from "$lib/components/Button.svelte";
  import { api } from "$lib/api/index";

  interface Props {
    framilies?: FramilyInfo[];
    framilyCodes?: string[];
    onClose?: () => void;
  }

  let { framilies = [], framilyCodes = [], onClose }: Props = $props();

  let fileInput: HTMLInputElement | undefined = $state();

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

  async function getSelectedFramilyCodes() {
    const framilyCheckboxes = document.querySelectorAll(
      ".framily-checkbox",
    ) as NodeListOf<HTMLInputElement>;
    return Array.from(framilyCheckboxes)
      .filter((checkbox) => checkbox.checked)
      .map((checkbox) => checkbox.id.replace("framily-", ""));
  }

  async function handleUpload() {
    if (fileInput && fileInput.files && fileInput.files.length > 0) {
      const file = fileInput.files[0];

      showMessage("Uploading...", "info", null);

      const selectedFramilyCodes = await getSelectedFramilyCodes();
      if (selectedFramilyCodes.length === 0) {
        showMessage("Please select at least one framily", "error");
        return;
      }

      try {
        await api.pictures.upload(selectedFramilyCodes, file);
        showMessage("Upload successful", "success");
      } catch (e: any) {
        showMessage(e.message || "Failed to upload", "error");
      } finally {
        if (fileInput) fileInput.value = "";
      }
    } else {
      showMessage("No file selected", "error");
    }
  }
</script>

<Popup {onClose}>
  <div class="content">
    {#if message}
      <div class="message {messageType}">{message}</div>
    {/if}
    <UploadZone bind:fileInput />
    <div class="framilies">
      {#each framilies as framily}
        <input
          class="framily-checkbox"
          type="checkbox"
          id={"framily-" + framily.code}
          checked={framilyCodes.includes(framily.code)}
        />
        <label class="framily-label" for={"framily-" + framily.code}
          >{framily.name}</label
        >
      {/each}
    </div>
    <div class="buttons">
      <Button onclick={onClose} color="#b8d9f2">Cancel</Button>
      <Button onclick={handleUpload}>Upload</Button>
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

  .framily-checkbox:checked + .framily-label {
    background-color: #4593e7;
    color: white;
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
