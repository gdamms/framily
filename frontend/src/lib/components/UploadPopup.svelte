<script lang="ts">
  import Popup from "$lib/components/Popup.svelte";
  import UploadZone from "$lib/components/UploadZone.svelte";

  interface Props {
    onClose?: () => void;
  }

  let { onClose }: Props = $props();
</script>

<Popup onClose={onClose}>
  <UploadZone />
</Popup>
