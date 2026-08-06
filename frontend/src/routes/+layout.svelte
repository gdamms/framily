<script lang="ts">
  import favicon from "$lib/assets/favicon.svg";
  import Overlay from "$lib/ui/Overlay.svelte";

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
    background-color: #f5f5f5;
    display: flex;
    flex-direction: column;
  }

  main {
    height: 100dvh;
    background: #bbb;
  }
</style>
