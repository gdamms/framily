<script lang="ts">
  import favicon from "$lib/assets/favicon.svg";
  import Overlay from "$lib/ui/Overlay.svelte";
  import "$lib/theme.css";
  import { themeStore } from "$lib/stores/theme";

  // Imported for its side effect: keeps <html data-theme> in sync with the
  // stored preference/system setting for the lifetime of the app.
  void themeStore;

  let { children } = $props();
</script>

<svelte:head>
  <link rel="icon" href={favicon} />
</svelte:head>

<main>
  {@render children()}
  <Overlay />
</main>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    font-family: Arial, sans-serif;
    background-color: var(--color-bg);
    color: var(--color-text);
    display: flex;
    flex-direction: column;
  }

  main {
    height: 100dvh;
    background: var(--color-bg-outer);
  }
</style>
