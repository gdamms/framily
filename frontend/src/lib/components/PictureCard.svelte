<script lang="ts">
  import type { PictureInfo } from "$lib/api";
  import { authStore } from "$lib/stores/auth";
  import { api } from "$lib/api";
  import FramilyTag from "./FramilyTag.svelte";
  import UserTag from "./UserTag.svelte";

  interface Props {
    picture: PictureInfo;
  }

  let { picture }: Props = $props();

  function fetchImageOnError(event: Event): void {
    const img = event.target as HTMLImageElement;
    img.onerror = null;
    const src = img.src;
    const options = {
      headers: {
        Authorization: `Bearer ${authStore.getToken()}`,
      },
    };
    fetch(src, options)
      .then((response) => response.blob())
      .then((blob) => {
        img.src = URL.createObjectURL(blob);
      });
  }
</script>

<div class="picture-card">
  <img
    class="picture-image"
    src={api.pictures.getImageUrl(picture)}
    alt="Uploaded by {picture.uploader_display_name}"
    onerror={fetchImageOnError}
  />
  <div class="tags">
    {#each picture.framilies as framily}
      <FramilyTag framilyCode={framily.code} framilyName={framily.name} />
    {/each}
    <UserTag username={picture.uploader_username} displayName={picture.uploader_display_name} />
  </div>
</div>

<style>
  .picture-card {
    position: relative;
    width: 100%;
    height: 100%;
  }

  .picture-image {
    width: 100%;
    height: 100%;
    object-fit: cover;
  }

  .tags {
    position: absolute;
    display: flex;
    direction: row-reverse;
    flex-wrap: wrap-reverse;
    bottom: 0;
    right: 0;
  }
</style>
