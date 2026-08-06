<script lang="ts">
  import { api, type PictureInfo } from "$lib/api";
  import Masonry from "$lib/ui/Masonry.svelte";
  import { app } from "$lib/app";

  interface Props {
    pictures: PictureInfo[];
  }

  let { pictures }: Props = $props();

  function getAspectRatio(picture: PictureInfo): number | undefined {
    const { width, height } = picture.metadata ?? {};
    if (!width || !height) return undefined;
    return width / height;
  }
</script>

<div class="galery">
  <Masonry items={pictures} {getAspectRatio}>
    {#snippet children(picture: PictureInfo)}
      <button
        class="picture-button"
        onclick={() => app.navigate({ page: "picture", picture })}
      >
        <img
          class="picture"
          src={api.pictures.getImageUrl(picture)}
          alt={picture.id}
          style={getAspectRatio(picture)
            ? `aspect-ratio: ${getAspectRatio(picture)}`
            : undefined}
        />
      </button>
    {/snippet}
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
