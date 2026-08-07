<script lang="ts">
  import { untrack } from "svelte";
  import type { UserFramilyInfo } from "$lib/api";
  import UploadZone from "$lib/ui/UploadZone.svelte";
  import Button from "$lib/ui/Button.svelte";
  import StatusMessage from "$lib/ui/StatusMessage.svelte";
  import { createStatusMessage } from "$lib/ui/statusMessage.svelte";
  import { api } from "$lib/api";

  interface Props {
    framilies?: UserFramilyInfo[];
    framilyCodes?: string[];
    onUploaded?: () => void;
    close?: () => void;
  }

  let { framilies = [], framilyCodes = [], onUploaded, close = () => {} }: Props = $props();

  let fileInput: HTMLInputElement | undefined = $state();

  // Each UploadPopup instance is freshly mounted per overlay.open() call, so
  // these props never change over its lifetime - read once, intentionally.
  let selected: Record<string, boolean> = $state(
    untrack(() => {
      const defaultCodes = new Set(framilyCodes);
      return Object.fromEntries(
        framilies.map((framily) => [framily.code, defaultCodes.has(framily.code)]),
      );
    }),
  );

  const status = createStatusMessage();

  async function handleUpload() {
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
      status.show("No file selected", "error");
      return;
    }

    const file = fileInput.files[0];
    status.show("Uploading...", "info", null);

    const selectedFramilyCodes = Object.entries(selected)
      .filter(([, checked]) => checked)
      .map(([code]) => code);
    if (selectedFramilyCodes.length === 0) {
      status.show("Please select at least one framily", "error");
      return;
    }

    try {
      await api.pictures.upload(selectedFramilyCodes, file);
      status.show("Upload successful", "success");
      onUploaded?.();
    } catch (e: any) {
      status.show(e.message || "Failed to upload", "error");
    } finally {
      fileInput.value = "";
      fileInput.dispatchEvent(new Event("change"));
    }
  }
</script>

<div class="content">
  <StatusMessage text={status.text} type={status.type} />
  <UploadZone bind:fileInput />
  <div class="framilies">
    {#each framilies as framily}
      <input
        class="framily-checkbox"
        type="checkbox"
        id={"framily-" + framily.code}
        bind:checked={selected[framily.code]}
      />
      <label class="framily-label" for={"framily-" + framily.code}>{framily.name}</label>
    {/each}
  </div>
  <div class="buttons">
    <Button variant="secondary" onclick={close}>Cancel</Button>
    <Button variant="primary" onclick={handleUpload}>Upload</Button>
  </div>
</div>

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

  .buttons {
    display: flex;
    gap: 10px;
  }
</style>
