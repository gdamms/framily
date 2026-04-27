<script lang="ts">
  import { onMount, type Snippet, tick } from "svelte";

  interface MasonryProps {
    children: Snippet;
    num?: number;
  }

  let { children, num = 3 }: MasonryProps = $props();

  let masonryChildren: HTMLDivElement | undefined = $state();
  let items: HTMLElement[] = $state([]);

  onMount(async () => {
    const observer = new MutationObserver((mutations) => {
      const columns = document.querySelectorAll(".masonry-column");
      items = Array.from(masonryChildren?.children || []) as HTMLElement[];
      for (let i = 0; i < items.length; i++) {
        const columnIndex = i % num;
        columns[columnIndex].appendChild(items[i]);
      }
    });
    if (masonryChildren) {
      observer.observe(masonryChildren, { childList: true });
    }
  });

  $effect(() => {});
</script>

<div class="masonry">
  <div bind:this={masonryChildren} class="masonry-children">
    {@render children()}
  </div>
  {#each Array(num) as _, i}
    <div class="masonry-column"></div>
  {/each}
</div>

<style>
  .masonry {
    flex: 1;
    display: flex;
    flex-direction: row;
    gap: 6px;
  }

  .masonry-children {
    display: none;
  }

  .masonry-column {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
</style>
