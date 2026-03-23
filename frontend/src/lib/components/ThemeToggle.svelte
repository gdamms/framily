<script lang="ts">
  import { themeStore } from "$lib/stores/theme";

  function toggleTheme() {
    themeStore.toggle();
  }
</script>

<button class="theme-toggle" on:click={toggleTheme} aria-label="Toggle theme">
  {#if $themeStore === "light"}
    🌞
  {:else}
    🌜
  {/if}
</button>

<style>
  .theme-toggle {
    background: none;
    border: none;
    cursor: pointer;
    font-size: 1.5rem;
    padding: 0.5rem;
    color: var(--color-text);
  }
</style>
