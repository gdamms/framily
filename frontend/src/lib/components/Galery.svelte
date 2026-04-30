<script lang="ts">
  import { api, type PictureInfo } from "$lib/api";
  import Masonry from "./Masonry.svelte";
  import { app } from "$lib/app";

  interface Props {
    pictures: PictureInfo[];
  }

  let { pictures }: Props = $props();
</script>

<div class="galery">
  <Masonry>
    {#each pictures as picture}
      <button
        class="picture-button"
        onclick={() => app.navigate({ page: "picture", id: picture.id })}
      >
        <img
          class="picture"
          src={api.pictures.getImageUrl(picture)}
          alt={picture.id}
        />
      </button>
    {/each}
  </Masonry>
</div>

<style>
  .picture-button {
    border: none;
    padding: 0;
    background: none;
    cursor: pointer;
    width: 100%;
  }

  .picture {
    width: 100%;
  }
</style>
