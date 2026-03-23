<script lang="ts">
  import favicon from "$lib/assets/favicon.svg";
  import { authStore } from "$lib/stores/auth";
  import Nav from "$lib/components/Nav.svelte";

  let { children } = $props();
</script>

<svelte:head>
  <link rel="icon" href={favicon} />
</svelte:head>

<main>
  {@render children()}
</main>

{#if $authStore.isAuthenticated}
  <Nav />
{/if}

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    font-family: Arial, sans-serif;
    background-color: #f5f5f5;
    height: 100vh;
    display: flex;
    flex-direction: column;
  }

  main {
    flex: 1;
  }
</style>
