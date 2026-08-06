<script lang="ts">
  import { api, type PictureInfo, type UserFramilyInfo } from "$lib/api";
  import Masonry from "$lib/ui/Masonry.svelte";
  import { overlay } from "$lib/overlay";
  import PictureView from "$lib/pages/picture/PictureView.svelte";

  interface Props {
    pictures: PictureInfo[];
    currentUsername: string;
    myFramilies: UserFramilyInfo[];
  }

  let { pictures, currentUsername, myFramilies }: Props = $props();

  function openPicture(picture: PictureInfo) {
    overlay.open(PictureView, { picture, currentUsername, myFramilies });
  }

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
        onclick={() => openPicture(picture)}
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
