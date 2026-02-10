<script lang="ts">
  import type { PictureInfo } from "$lib/api";
  import PictureCard from "./PictureCard.svelte";

  interface Props {
    pictures: PictureInfo[];
  }

  let { pictures = [] }: Props = $props();
</script>

<div class="galery">
  {#each pictures as picture}
    <PictureCard {picture} />
  {/each}
</div>

<style>
  .galery {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 1rem;
  }
</style>