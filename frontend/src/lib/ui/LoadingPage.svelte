<script lang="ts">
  import type { Snippet } from "svelte";

  interface Props {
    children?: Snippet;
  }

  let { children }: Props = $props();
</script>

<div class="loading-page">
  {#if children}
    {@render children()}
  {:else}
    Loading...
  {/if}
</div>

<style>
  .loading-page {
    flex: 1;
    min-height: 0;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 1rem;
    color: var(--color-text-muted);
  }
</style>
