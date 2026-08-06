<script lang="ts">
  import { onMount, tick } from "svelte";
  import { api, type FramilyInfo, type PictureInfo } from "$lib/api";
  import Galery from "./Galery.svelte";
  import Members from "./Members.svelte";
  import FramilySettings from "./FramilySettings.svelte";
  import Avatar from "./Avatar.svelte";
  import { app } from "$lib/app";
  import ImagePlus from "@lucide/svelte/icons/image-plus";
  import Pencil from "@lucide/svelte/icons/pencil";

  interface Props {
    code: string;
    currentUsername: string;
    onAddPicture?: (framilyCode: string) => void;
    onFramilyDeleted?: () => void;
  }

  let { code, currentUsername, onAddPicture, onFramilyDeleted }: Props = $props();

  let appState = app.state;

  let framily: FramilyInfo | undefined = $state();
  let pictures: PictureInfo[] = $state([]);

  let isAdmin = $derived(
    framily?.members.find((m) => m.username === currentUsername)?.role === "admin",
  );

  let editingName = $state(false);
  let nameDraft = $state("");
  let nameInputEl: HTMLInputElement | undefined = $state();

  function startEditingName() {
    if (!isAdmin || !framily) return;
    nameDraft = framily.name ?? "";
    editingName = true;
    tick().then(() => nameInputEl?.focus());
  }

  async function saveName() {
    if (!editingName || !framily) return;
    editingName = false;
    const trimmed = nameDraft.trim();
    if (!trimmed || trimmed === framily.name) return;
    await api.framily.updateSettings(framily.code, { name: trimmed });
    await loadFramily();
  }

  function handleNameKeydown(event: KeyboardEvent) {
    if (event.key === "Enter") {
      event.preventDefault();
      (event.target as HTMLInputElement).blur();
    } else if (event.key === "Escape") {
      editingName = false;
    }
  }

  async function loadFramily() {
    framily = await api.framily.info(code);

    let picResponse = await api.pictures.list({
      framily_code: framily.code,
    });
    pictures = picResponse.pictures;
  }

  onMount(loadFramily);
</script>

{#if framily === undefined}
  <div class="framily-page">Loading...</div>
{:else if $appState.page.page !== "framily"}
  <div class="framily-page">Framily not found</div>
{:else}
  <div class="framily-page">
    <div class="framily-header">
      <Avatar kind="framily" id={framily.code} label={framily.name ?? framily.code} editable={isAdmin} size={64} />
      <div class="framily-names">
        {#if isAdmin && editingName}
          <input
            class="framily-name-input"
            bind:value={nameDraft}
            bind:this={nameInputEl}
            onblur={saveName}
            onkeydown={handleNameKeydown}
          />
        {:else if isAdmin}
          <button class="framily-name editable" onclick={startEditingName}>
            <span>{framily.name}</span>
            <Pencil size={16} />
          </button>
        {:else}
          <div class="framily-name">{framily.name}</div>
        {/if}
        <div class="framily-code">@{framily.code}</div>
      </div>
    </div>
    <div class="framily-nav">
      <button
        class="button"
        class:selected={$appState.page.section === "pictures"}
        onclick={() => (app.navigate({ page: "framily", code: framily!.code, section: "pictures" }))}
      >
        Pictures
      </button>
      <button
        class="button"
        class:selected={$appState.page.section === "members"}
        onclick={() => (app.navigate({ page: "framily", code: framily!.code, section: "members" }))}
      >
        Members
      </button>
      <button
        class="button"
        class:selected={$appState.page.section === "settings"}
        onclick={() => (app.navigate({ page: "framily", code: framily!.code, section: "settings" }))}
      >
        Settings
      </button>
    </div>
    <div class="framily-content">
      {#if $appState.page.section === "pictures"}
        {#if onAddPicture}
          <button class="add-picture" onclick={() => onAddPicture?.(framily!.code)}>
            <ImagePlus size={16} />
            Add picture
          </button>
        {/if}
        <Galery {pictures} />
      {:else if $appState.page.section === "members"}
        <Members
          framilyCode={framily.code}
          members={framily.members}
          {currentUsername}
          onChanged={loadFramily}
        />
      {:else if $appState.page.section === "settings"}
        <FramilySettings
          {framily}
          {currentUsername}
          onChanged={loadFramily}
          onDeleted={() => {
            onFramilyDeleted?.();
            app.navigate({ page: "dashboard", section: "framilies" });
          }}
        />
      {/if}
    </div>
  </div>
{/if}

<style>
  .framily-page {
    flex: 1;
    min-height: 0;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .framily-header {
    background: #eee;
    padding: 0 1rem;
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .framily-names {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }

  .framily-name {
    font-size: 24px;
    font-weight: bold;
  }

  button.framily-name.editable {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    background: none;
    border: none;
    padding: 0;
    cursor: pointer;
    color: inherit;
    font-family: inherit;
  }

  .framily-name-input {
    font-size: 24px;
    font-weight: bold;
    font-family: inherit;
    border: none;
    border-bottom: 2px solid #333;
    background: none;
    padding: 0;
    max-width: 100%;
  }

  .framily-code {
    font-size: 14px;
    color: #666;
  }

  .framily-nav {
    display: flex;
    flex-direction: row;
    padding: 0.5rem 0;
  }

  .button {
    background: none;
    border: none;
    padding: 0.5rem 1rem;
    cursor: pointer;
    flex: 1;
  }

  .button.selected {
    font-weight: bold;
    border-bottom: 2px solid #333;
  }

  .framily-content {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .add-picture {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    align-self: flex-start;
    background-color: #28a745;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 0.5rem 1rem;
    cursor: pointer;
    margin: 1rem 1rem 0;
  }
</style>
