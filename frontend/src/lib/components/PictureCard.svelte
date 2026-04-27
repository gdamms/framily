<script lang="ts">
  import type { PictureInfo } from "$lib/api";
  import { api } from "$lib/api";
  import { goto } from "$app/navigation";

  interface Props {
    picture: PictureInfo;
  }

  let { picture }: Props = $props();

  async function fetchImageOnError(event: Event): Promise<void> {
    const img = event.target as HTMLImageElement;
    img.onerror = null;

    try {
      const blob = await api.pictures.getImageBlob(picture.id);
      img.src = URL.createObjectURL(blob);
    } catch {
      // Keep the original failed image source.
    }
  }

  function gotoPictureDetail() {
    goto(`/picture/${picture.id}`);
  }
</script>

<button class="picture-card-button" onclick={gotoPictureDetail}>
  <img
    class="picture-card"
    src={api.pictures.getImageUrl(picture)}
    alt="Uploaded by {picture.uploader_display_name}"
    onerror={fetchImageOnError}
  />
</button>

<style>
  .picture-card-button {
    padding: 0;
    border: none;
    background: none;
    cursor: pointer;
  }

  .picture-card {
    width: 100%;
    height: 100%;
    object-fit: cover;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    transform-origin: center;
    transition:
      transform 0.2s ease,
      box-shadow 0.2s ease;
  }

  .picture-card:hover {
    transform: scale(1.1);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
  }
</style>
