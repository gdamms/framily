<script lang="ts">
  import { tick, onDestroy } from "svelte";
  import { api, type PictureInfo, type UserFramilyInfo } from "$lib/api";
  import { CAPTION_MAX_LENGTH } from "$lib/api/types";
  import X from "@lucide/svelte/icons/x";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import Plus from "@lucide/svelte/icons/plus";
  import Pencil from "@lucide/svelte/icons/pencil";
  import { overlay } from "$lib/overlay";
  import ConfirmPopup from "$lib/popups/ConfirmPopup.svelte";
  import IconButton from "$lib/ui/IconButton.svelte";
  import { formatDate } from "$lib/date";

  interface Props {
    picture: PictureInfo;
    currentUsername: string;
    myFramilies: UserFramilyInfo[];
    onChanged?: () => void;
    close?: () => void;
  }

  let { picture, currentUsername, myFramilies, onChanged, close = () => {} }: Props = $props();

  let framilies = $state(picture.framilies);

  let error = $state("");
  let showAddPicker = $state(false);

  let isUploader = $derived(picture.uploader_username === currentUsername);
  let adminCodes = $derived(
    new Set(myFramilies.filter((f) => f.role === "admin").map((f) => f.code)),
  );
  let addableFramilies = $derived(
    myFramilies.filter(
      (f) => f.role !== "invited" && !framilies.some((pf) => pf.code === f.code),
    ),
  );

  function canRemoveFrom(code: string): boolean {
    return isUploader || adminCodes.has(code);
  }

  async function removeFrom(code: string) {
    error = "";
    try {
      await api.pictures.removeVisibility(picture.id, [code]);
      framilies = framilies.filter((f) => f.code !== code);
      onChanged?.();
    } catch (e: any) {
      error = e.message || "Failed to remove from framily";
    }
  }

  async function addTo(framily: UserFramilyInfo) {
    error = "";
    try {
      await api.pictures.addVisibility(picture.id, [framily.code]);
      framilies = [...framilies, { code: framily.code, name: framily.name ?? framily.code }];
      showAddPicker = false;
      onChanged?.();
    } catch (e: any) {
      error = e.message || "Failed to add to framily";
    }
  }

  async function deleteEntirely() {
    error = "";
    try {
      await api.pictures.delete(picture.id);
      onChanged?.();
      close();
    } catch (e: any) {
      error = e.message || "Failed to delete picture";
    }
  }

  function confirmDelete() {
    overlay.open(ConfirmPopup, {
      prompt: "Delete this picture entirely? This cannot be undone.",
      onConfirm: deleteEntirely,
    });
  }

  let editingCaption = $state(false);
  let captionDraft = $state("");
  let captionInputEl: HTMLInputElement | undefined = $state();
  let captionSaveTimeout: ReturnType<typeof setTimeout> | undefined;

  const CAPTION_SAVE_DEBOUNCE_MS = 500;

  function startEditingCaption() {
    if (!isUploader) return;
    captionDraft = picture.description ?? "";
    editingCaption = true;
    tick().then(() => captionInputEl?.focus());
  }

  function scheduleCaptionSave() {
    clearTimeout(captionSaveTimeout);
    captionSaveTimeout = setTimeout(commitCaption, CAPTION_SAVE_DEBOUNCE_MS);
  }

  async function commitCaption() {
    clearTimeout(captionSaveTimeout);
    captionSaveTimeout = undefined;
    const trimmed = captionDraft.trim();
    if (trimmed === (picture.description ?? "")) return;
    error = "";
    try {
      const response = await api.pictures.updateDescription(picture.id, trimmed);
      // Mutate the picture prop in place (rather than local component state)
      // so the caption stays up to date in whatever list handed us this
      // picture object - otherwise reopening it later shows the stale value.
      picture.description = response.picture.description ?? null;
    } catch (e: any) {
      error = e.message || "Failed to update caption";
    }
  }

  function finishEditingCaption() {
    commitCaption();
    editingCaption = false;
  }

  function handleCaptionKeydown(event: KeyboardEvent) {
    if (event.key === "Enter") {
      event.preventDefault();
      (event.target as HTMLInputElement).blur();
    } else if (event.key === "Escape") {
      clearTimeout(captionSaveTimeout);
      captionSaveTimeout = undefined;
      editingCaption = false;
    }
  }

  onDestroy(() => {
    // Flush a pending debounced edit if the popup gets closed mid-type -
    // it's unmounted rather than blurred in that case, so blur never fires.
    if (captionSaveTimeout) commitCaption();
  });
</script>

<div class="picture-view">
  <div class="details">
    <div class="meta">
      <div class="meta-text">
        <span class="uploader"
          >{picture.uploader_display_name || picture.uploader_username}</span
        >
        <span class="date">{formatDate(picture.upload_date)}</span>
      </div>
      <div class="meta-actions">
        {#if isUploader}
          <IconButton icon={Trash2} variant="danger" label="Delete entirely" onclick={confirmDelete} />
        {/if}
        <IconButton icon={X} onclick={close} />
      </div>
    </div>

    {#if error}
      <p class="error">{error}</p>
    {/if}

    {#if isUploader || picture.description}
      <div class="caption-section">
        {#if editingCaption}
          <input
            class="caption-input"
            bind:value={captionDraft}
            bind:this={captionInputEl}
            maxlength={CAPTION_MAX_LENGTH}
            placeholder="Add a caption"
            oninput={scheduleCaptionSave}
            onblur={finishEditingCaption}
            onkeydown={handleCaptionKeydown}
          />
        {:else if picture.description}
          <button
            class="caption editable"
            class:readonly={!isUploader}
            onclick={startEditingCaption}
            disabled={!isUploader}
          >
            <span class="caption-text">{picture.description}</span>
            {#if isUploader}
              <Pencil size={14} />
            {/if}
          </button>
        {:else}
          <button class="caption-add" onclick={startEditingCaption}>
            <Pencil size={14} />
            Add a caption
          </button>
        {/if}
      </div>
    {/if}

    <div class="framily-chips">
      {#if isUploader && addableFramilies.length > 0}
        <button class="chip chip-add" onclick={() => (showAddPicker = !showAddPicker)}>
          <Plus size={14} />
          Add to framily
        </button>
      {/if}
      {#each framilies as framily}
        <span class="chip">
          {framily.name}
          {#if canRemoveFrom(framily.code)}
            <button
              class="chip-remove"
              title="Remove from {framily.name}"
              onclick={() => removeFrom(framily.code)}
            >
              <X size={14} />
            </button>
          {/if}
        </span>
      {/each}
    </div>

    {#if showAddPicker}
      <div class="add-picker">
        {#each addableFramilies as framily}
          <button class="add-option" onclick={() => addTo(framily)}>
            {framily.name}
          </button>
        {/each}
      </div>
    {/if}
  </div>

  <div class="image-wrapper">
    <img
      class="image"
      src={api.pictures.getImageUrl(picture)}
      alt="Uploaded by {picture.uploader_display_name || picture.uploader_username}"
    />
  </div>
</div>

<style>
  .picture-view {
    display: flex;
    flex-direction: column;
    background: white;
    border-radius: 12px;
    overflow: hidden;
  }

  .image-wrapper {
    position: relative;
    background: #111;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .image {
    max-width: 100%;
    max-height: 60vh;
    object-fit: contain;
  }

  .details {
    box-sizing: border-box;
    padding: 0.75rem 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    background: white;
  }

  .meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 0.5rem;
  }

  .meta-text {
    display: flex;
    flex-direction: column;
    min-width: 0;
  }

  .meta-actions {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    flex: 0 0 auto;
  }

  .uploader {
    font-weight: bold;
  }

  .date {
    color: #666;
    font-size: 0.85rem;
    white-space: nowrap;
  }

  .error {
    color: #dc3545;
    margin: 0;
  }

  .caption-section {
    display: flex;
    min-width: 0;
  }

  .caption {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    text-align: left;
    background: none;
    border: none;
    padding: 0;
    cursor: pointer;
    color: #333;
    font: inherit;
    min-width: 0;
    max-width: 100%;
  }

  .caption.readonly {
    cursor: default;
  }

  .caption-text {
    white-space: nowrap;
    overflow-x: auto;
  }

  .caption-add {
    display: inline-flex;
    align-items: center;
    gap: 0.4rem;
    background: none;
    border: none;
    padding: 0;
    cursor: pointer;
    color: #888;
    font: inherit;
    font-size: 0.9rem;
  }

  .caption-input {
    width: 100%;
    box-sizing: border-box;
    padding: 0.4rem 0;
    border: none;
    border-bottom: 2px solid #333;
    font: inherit;
    background: none;
  }

  .framily-chips {
    display: flex;
    flex-wrap: nowrap;
    overflow-x: auto;
    gap: 0.5rem;
  }

  .chip {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
    flex: 0 0 auto;
    white-space: nowrap;
    background: #e3f2fd;
    color: #1976d2;
    padding: 0.35rem 0.6rem;
    border-radius: 999px;
    font-size: 0.85rem;
    border: none;
  }

  .chip-remove {
    background: none;
    border: none;
    color: inherit;
    display: flex;
    cursor: pointer;
    padding: 0;
  }

  .chip-add {
    background: #eee;
    color: #333;
    cursor: pointer;
  }

  .add-picker {
    display: flex;
    flex-wrap: nowrap;
    overflow-x: auto;
    gap: 0.5rem;
  }

  .add-option {
    flex: 0 0 auto;
    white-space: nowrap;
    background: #c8dadf;
    border: none;
    padding: 0.35rem 0.6rem;
    border-radius: 6px;
    cursor: pointer;
  }

</style>
