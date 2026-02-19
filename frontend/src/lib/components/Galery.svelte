<script lang="ts">
  import type { FramilyInfo, PictureInfo } from "$lib/api";
  import PictureCard from "./PictureCard.svelte";
  import UploadPopup from "./UploadPopup.svelte";
  import UploadButton from "./UploadButton.svelte";

  interface Props {
    pictures: PictureInfo[];
    framilies: FramilyInfo[];
  }

  let { pictures, framilies }: Props = $props();

  let uploadPopupOpen = $state(false);

  function uploadPopupToggle() {
    uploadPopupOpen = !uploadPopupOpen;
  }
</script>

<div class="galery">
  {#each pictures as picture}
    <PictureCard {picture} />
  {/each}
  <div class="upload-btn">
    <UploadButton onclick={uploadPopupToggle} />
  </div>
  {#if uploadPopupOpen}
    <UploadPopup onClose={uploadPopupToggle} framilies={framilies} framilyCodes={[]} />
  {/if}
</div>

<style>
  .galery {
    position: relative;
    padding: 1rem;
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 0.5rem;
  }

  .upload-btn {
    position: fixed;
    bottom: 1rem;
    right: 1rem;
  }
</style>