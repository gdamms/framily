<script lang="ts">
  import IconButton from "$lib/components/IconButton.svelte";
  import { ImageUp } from "@lucide/svelte";

  interface Props {
    onclick?: (() => void);
  }

  let {
    onclick,
  }: Props = $props();
</script>

<IconButton icon={ImageUp} {onclick}/>
