<script lang="ts">
  import Button from "$lib/components/Button.svelte";
  import { type Icon as IconType } from "@lucide/svelte";

  interface Props {
    icon: typeof IconType;
    onclick?: (() => void);
    type?: "button" | "submit" | "reset";
    color?: string;
    class?: string;
  }

  let {
    icon,
    onclick,
    type,
    color,
    class: _class,
  }: Props = $props();
</script>

<Button class={"iconButton " + (_class ?? "")} onclick={onclick} type={type} color={color}>
  {@const Icon = icon}
  <Icon />
</Button>

<style>
  :global(.iconButton) {
    width: 3rem;
    aspect-ratio: 1 / 1;
  }
</style>
