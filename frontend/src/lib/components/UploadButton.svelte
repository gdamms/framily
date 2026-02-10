<script lang="ts">
  import IconButton from "$lib/components/IconButton.svelte";
  import { ImageUp } from "@lucide/svelte";

  interface Props {
    onclick?: (() => void);
    class?: string;
  }

  let {
    onclick,
    class: _class,
  }: Props = $props();
</script>

<IconButton class={_class} icon={ImageUp} {onclick}/>
