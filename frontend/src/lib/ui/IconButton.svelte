<script lang="ts">
  import Button from "./Button.svelte";
  import { type Icon as IconType } from "@lucide/svelte";

  interface Props {
    icon: typeof IconType;
    onclick?: () => void;
    type?: "button" | "submit" | "reset";
    variant?: "primary" | "secondary" | "danger" | "ghost";
    size?: number;
    label?: string;
  }

  let { icon: Icon, onclick, type, variant = "ghost", size = 20, label }: Props = $props();
</script>

<Button {onclick} {type} {variant} class="icon-btn" >
  <Icon size={size} aria-label={label} />
</Button>

<style>
  :global(.icon-btn) {
    padding: 0.6rem;
    border-radius: 999px;
  }
</style>
