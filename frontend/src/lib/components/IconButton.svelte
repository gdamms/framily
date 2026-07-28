<script lang="ts">
  import Button from "$lib/components/Button.svelte";
  import { type Icon as IconType } from "@lucide/svelte";

  interface Props {
    icon: typeof IconType;
    onclick?: (() => void);
    type?: "button" | "submit" | "reset";
    color?: string;
  }

  let {
    icon,
    onclick,
    type,
    color,
  }: Props = $props();

  let Icon: typeof IconType = $derived(icon);
</script>

<div class="icon-btn">
  <Button onclick={onclick} type={type} color={color}>
    <Icon />
  </Button>
</div>

<style>
  .icon-btn {
    width: 3rem;
    aspect-ratio: 1 / 1;
  }
</style>
