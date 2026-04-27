<script lang="ts">
  import { api, type PictureInfo } from "$lib/api";
  import Masonry from "./Masonry.svelte";

  interface Props {
    pictures: PictureInfo[];
  }

  let { pictures }: Props = $props();
</script>

<div class="galery">
  <Masonry>
    {#each pictures as picture}
      <img
        class="picture"
        src={api.pictures.getImageUrl(picture)}
        alt={picture.id}
      />
    {/each}
  </Masonry>
</div>

<style>
  .picture {
    width: 100%;
  }
</style>
