<script lang="ts">
  import Menu from "@lucide/svelte/icons/menu";
  import X from "@lucide/svelte/icons/x";
  import IconButton from "./IconButton.svelte";

  interface Props {
    isOpen: boolean;
    onclick?: () => void;
  }

  let { isOpen, onclick }: Props = $props();
</script>

<IconButton icon={isOpen ? X : Menu} onclick={onclick} />
