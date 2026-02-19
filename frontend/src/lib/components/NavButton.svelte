<script lang="ts">
  import { Menu, X } from "@lucide/svelte";
  import IconButton from "./IconButton.svelte";

  interface Props {
    isOpen: boolean;
    onclick?: () => void;
  }

  let { isOpen, onclick }: Props = $props();
</script>

<IconButton icon={isOpen ? X : Menu} onclick={onclick} />
