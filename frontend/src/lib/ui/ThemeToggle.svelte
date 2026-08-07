<script lang="ts">
  import { themeStore } from "$lib/stores/theme";
  import Sun from "@lucide/svelte/icons/sun";
  import Moon from "@lucide/svelte/icons/moon";

  interface Props {
    size?: number;
  }

  let { size = 20 }: Props = $props();

  const preference = themeStore.preference;

  const LABEL = {
    system: "Theme: system",
    light: "Theme: light",
    dark: "Theme: dark",
  } as const;
</script>

<button
  class="theme-toggle"
  type="button"
  onclick={() => themeStore.cycle()}
  title={LABEL[$preference]}
  aria-label={LABEL[$preference]}
>
  {#if $preference === "system"}
    <span class="split-icon" style="width: {size}px; height: {size}px;">
      <span class="half half-sun">
        <Sun {size} />
      </span>
      <span class="half half-moon">
        <Moon {size} />
      </span>
    </span>
  {:else if $preference === "light"}
    <Sun {size} />
  {:else}
    <Moon {size} />
  {/if}
</button>

<style>
  .theme-toggle {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    border: none;
    border-radius: 999px;
    padding: 0.6rem;
    background-color: var(--color-theme-toggle-bg);
    color: var(--color-theme-toggle-icon);
    cursor: pointer;
    transition: transform 0.05s ease;
  }

  .theme-toggle:active {
    transform: scale(0.94);
  }

  .split-icon {
    position: relative;
    display: inline-block;
    pointer-events: none;
  }

  .half {
    position: absolute;
    inset: 0;
    display: flex;
  }

  /* Diagonal split from top-left to bottom-right: sun fills the bottom-left
     triangle, moon fills the top-right triangle. */
  .half-sun {
    clip-path: polygon(0 0, 0 100%, 100% 100%);
  }

  .half-moon {
    clip-path: polygon(0 0, 100% 0, 100% 100%);
  }
</style>
