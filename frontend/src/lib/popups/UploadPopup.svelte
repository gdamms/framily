<script lang="ts">
  import { m } from "$lib/i18n.svelte";
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
      status.show(m.upload_no_file(), "error");
      return;
    }

    const file = fileInput.files[0];
    status.show(m.common_uploading(), "info", null);

    const selectedFramilyCodes = Object.entries(selected)
      .filter(([, checked]) => checked)
      .map(([code]) => code);
    if (selectedFramilyCodes.length === 0) {
      status.show(m.upload_select_framily(), "error");
      return;
    }

    try {
      await api.pictures.upload(selectedFramilyCodes, file);
      status.show(m.upload_success(), "success");
      onUploaded?.();
    } catch (e: any) {
      status.show(e.message || m.common_upload_failed(), "error");
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
    <Button variant="secondary" onclick={close}>{m.common_cancel()}</Button>
    <Button variant="primary" onclick={handleUpload}>{m.common_upload()}</Button>
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
    background-color: var(--color-dropzone-bg);
    color: var(--color-text);
    border-radius: 5px;
    cursor: pointer;
    transition: background-color 0.3s ease;
  }

  .framily-checkbox:checked + .framily-label {
    background-color: var(--color-primary);
    color: var(--color-text-inverse);
  }

  .buttons {
    display: flex;
    gap: 10px;
  }
</style>
