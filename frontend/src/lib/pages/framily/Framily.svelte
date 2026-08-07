<script lang="ts">
  import { onMount, tick } from "svelte";
  import { api, type FramilyInfo, type PictureInfo, type UserFramilyInfo } from "$lib/api";
  import Galery from "$lib/components/Galery.svelte";
  import Members from "./Members.svelte";
  import FramilySettings from "./FramilySettings.svelte";
  import Avatar from "$lib/ui/Avatar.svelte";
  import PageLayout from "$lib/ui/PageLayout.svelte";
  import LoadingPage from "$lib/ui/LoadingPage.svelte";
  import { app } from "$lib/app";
  import { overlay } from "$lib/overlay";
  import UploadPopup from "$lib/popups/UploadPopup.svelte";
  import ImagePlus from "@lucide/svelte/icons/image-plus";
  import Pencil from "@lucide/svelte/icons/pencil";

  interface Props {
    code: string;
    currentUsername: string;
    framilies: UserFramilyInfo[];
    onFramilyDeleted?: () => void;
  }

  let { code, currentUsername, framilies, onFramilyDeleted }: Props = $props();

  let appState = app.state;

  let framily: FramilyInfo | undefined = $state();
  let pictures: PictureInfo[] = $state([]);

  let isAdmin = $derived(
    framily?.members.find((m) => m.username === currentUsername)?.role === "admin",
  );

  let editingName = $state(false);
  let nameDraft = $state("");
  let nameInputEl: HTMLInputElement | undefined = $state();

  const TABS = [
    { id: "pictures" as const, label: "Pictures" },
    { id: "members" as const, label: "Members" },
    { id: "settings" as const, label: "Settings" },
  ];

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

  function openUploadPopup() {
    if (!framily) return;
    overlay.open(UploadPopup, {
      framilies,
      framilyCodes: [framily.code],
      onUploaded: loadFramily,
    });
  }

  onMount(loadFramily);
</script>

{#if framily === undefined}
  <LoadingPage />
{:else if $appState.page.page !== "framily"}
  <div class="message">Framily not found</div>
{:else}
  {@const framilyPage = $appState.page}
  {#snippet header()}
    <div class="framily-header">
      <Avatar kind="framily" id={framily!.code} label={framily!.name ?? framily!.code} editable={isAdmin} size={64} />
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
            <span>{framily!.name}</span>
            <Pencil size={16} />
          </button>
        {:else}
          <div class="framily-name">{framily!.name}</div>
        {/if}
        <div class="framily-code">@{framily!.code}</div>
      </div>
    </div>
  {/snippet}

  {#snippet content()}
    {#if framilyPage.section === "pictures"}
      <button class="add-picture" onclick={openUploadPopup}>
        <ImagePlus size={16} />
        Add picture
      </button>
      <Galery {pictures} {currentUsername} myFramilies={framilies} onPictureChanged={loadFramily} />
    {:else if framilyPage.section === "members"}
      <Members
        framilyCode={framily!.code}
        members={framily!.members}
        {currentUsername}
        onChanged={loadFramily}
      />
    {:else if framilyPage.section === "settings"}
      <FramilySettings
        framily={framily!}
        {currentUsername}
        onChanged={loadFramily}
        onDeleted={() => {
          onFramilyDeleted?.();
          app.navigate({ page: "dashboard", section: "framilies" });
        }}
      />
    {/if}
  {/snippet}

  <PageLayout
    {header}
    tabs={TABS}
    selected={framilyPage.section}
    onSelect={(section) => app.navigate({ page: "framily", code: framily!.code, section })}
    {content}
  />
{/if}

<style>
  .message {
    flex: 1;
    padding: 1rem;
  }

  .framily-header {
    background: var(--color-bg-page);
    padding: 0 1rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
    width: 100%;
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
    border-bottom: 2px solid var(--color-text);
    background: none;
    color: var(--color-text);
    padding: 0;
    max-width: 100%;
  }

  .framily-code {
    font-size: 14px;
    color: var(--color-text-secondary);
  }

  .add-picture {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    align-self: flex-start;
    background-color: var(--color-success);
    color: var(--color-text-inverse);
    border: none;
    border-radius: 6px;
    padding: 0.5rem 1rem;
    cursor: pointer;
    margin: 1rem 1rem 0;
  }
</style>
