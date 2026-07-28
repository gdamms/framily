<script lang="ts">
  import { api, type PictureInfo, type UserFramilyInfo } from "$lib/api";
  import X from "@lucide/svelte/icons/x";
  import Trash2 from "@lucide/svelte/icons/trash-2";
  import Plus from "@lucide/svelte/icons/plus";
  import ConfirmPopup from "./ConfirmPopup.svelte";

  interface Props {
    picture: PictureInfo;
    currentUsername: string;
    myFramilies: UserFramilyInfo[];
    onClose: () => void;
  }

  let { picture, currentUsername, myFramilies, onClose }: Props = $props();

  let framilies = $state(picture.framilies);

  let error = $state("");
  let showAddPicker = $state(false);
  let confirmDeleteOpen = $state(false);

  let isUploader = $derived(picture.uploader_username === currentUsername);
  let adminCodes = $derived(
    new Set(myFramilies.filter((f) => f.role === 2).map((f) => f.code)),
  );
  let addableFramilies = $derived(
    myFramilies.filter(
      (f) => f.role >= 1 && !framilies.some((pf) => pf.code === f.code),
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
    } catch (e: any) {
      error = e.message || "Failed to add to framily";
    }
  }

  async function deleteEntirely() {
    error = "";
    try {
      await api.pictures.delete(picture.id);
      onClose();
    } catch (e: any) {
      error = e.message || "Failed to delete picture";
    }
  }
</script>

<ConfirmPopup
  bind:isOpen={confirmDeleteOpen}
  prompt="Delete this picture entirely? This cannot be undone."
  onConfirm={deleteEntirely}
/>

<div class="picture-view">
  <div class="top-bar">
    <button class="close-button" onclick={onClose}>
      <X />
    </button>
  </div>

  <div class="image-wrapper">
    <img
      class="image"
      src={api.pictures.getImageUrl(picture)}
      alt="Uploaded by {picture.uploader_display_name || picture.uploader_username}"
    />
  </div>

  <div class="details">
    <div class="meta">
      <span class="uploader"
        >{picture.uploader_display_name || picture.uploader_username}</span
      >
      <span class="date">{new Date(picture.upload_date).toLocaleDateString()}</span>
    </div>

    {#if error}
      <p class="error">{error}</p>
    {/if}

    <div class="framily-chips">
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
      {#if isUploader && addableFramilies.length > 0}
        <button class="chip chip-add" onclick={() => (showAddPicker = !showAddPicker)}>
          <Plus size={14} />
          Add to framily
        </button>
      {/if}
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

    {#if isUploader}
      <button class="delete-button" onclick={() => (confirmDeleteOpen = true)}>
        <Trash2 size={16} />
        Delete entirely
      </button>
    {/if}
  </div>
</div>

<style>
  .picture-view {
    position: fixed;
    inset: 0;
    background: #111;
    display: flex;
    flex-direction: column;
    z-index: 500;
  }

  .top-bar {
    display: flex;
    justify-content: flex-end;
    padding: 0.5rem;
  }

  .close-button {
    background: none;
    border: none;
    color: white;
    padding: 0.5rem;
    cursor: pointer;
    display: flex;
  }

  .image-wrapper {
    flex: 1;
    display: flex;
    align-items: center;
    justify-content: center;
    min-height: 0;
    padding: 0.5rem;
  }

  .image {
    max-width: 100%;
    max-height: 100%;
    object-fit: contain;
  }

  .details {
    background: white;
    border-radius: 12px 12px 0 0;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .meta {
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .uploader {
    font-weight: bold;
  }

  .date {
    color: #666;
    font-size: 0.85rem;
  }

  .error {
    color: #dc3545;
    margin: 0;
  }

  .framily-chips {
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .chip {
    display: inline-flex;
    align-items: center;
    gap: 0.35rem;
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
    flex-wrap: wrap;
    gap: 0.5rem;
  }

  .add-option {
    background: #c8dadf;
    border: none;
    padding: 0.35rem 0.6rem;
    border-radius: 6px;
    cursor: pointer;
  }

  .delete-button {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    background-color: #dc3545;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 0.6rem;
    cursor: pointer;
  }
</style>
