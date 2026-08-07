<script lang="ts">
  import { type UserFramilyInfo, type PictureInfo } from "$lib/api";
  import { app } from "$lib/app";
  import { overlay } from "$lib/overlay";
  import Galery from "$lib/components/Galery.svelte";
  import Framilies from "$lib/pages/framilies/Framilies.svelte";
  import PageLayout from "$lib/ui/PageLayout.svelte";
  import UploadPopup from "$lib/popups/UploadPopup.svelte";
  import ConnectFramilyPopup from "$lib/popups/ConnectFramilyPopup.svelte";
  import ImagePlus from "@lucide/svelte/icons/image-plus";

  interface Props {
    framilies: UserFramilyInfo[];
    pictures: PictureInfo[];
    section: "galery" | "framilies";
    currentUsername: string;
    onPicturesChanged?: () => void;
    onFramiliesChanged?: () => void;
  }

  let { framilies, pictures, section, currentUsername, onPicturesChanged, onFramiliesChanged }: Props = $props();

  const TABS = [
    { id: "galery" as const, label: "Galery" },
    { id: "framilies" as const, label: "My framilies" },
  ];

  function openUploadPopup() {
    overlay.open(UploadPopup, {
      framilies,
      framilyCodes: framilies.map((f) => f.code),
      onUploaded: onPicturesChanged,
    });
  }
</script>

{#snippet header()}
  <div class="dashboard-header">Framily</div>
{/snippet}

{#snippet content()}
  {#if section === "galery"}
    <button class="add-picture" onclick={openUploadPopup}>
      <ImagePlus size={16} />
      Add picture
    </button>
    <Galery {pictures} {currentUsername} myFramilies={framilies} onPictureChanged={onPicturesChanged} />
  {:else if section === "framilies"}
    <Framilies
      {framilies}
      onAddFramily={() => overlay.open(ConnectFramilyPopup, { onSuccess: onFramiliesChanged })}
      onFramilyChanged={onFramiliesChanged}
    />
  {/if}
{/snippet}

<PageLayout
  {header}
  tabs={TABS}
  selected={section}
  onSelect={(id) => app.navigate({ page: "dashboard", section: id })}
  {content}
/>

<style>
  .dashboard-header {
    padding: 0.5rem;
    font-weight: bold;
    font-size: 1.5rem;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
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
