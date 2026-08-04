<script lang="ts" generics="T">
  import type { Snippet } from "svelte";

  interface MasonryProps<T> {
    items: T[];
    children: Snippet<[T]>;
    num?: number;
    getAspectRatio?: (item: T) => number | null | undefined;
  }

  const DEFAULT_ASPECT_RATIO = 1;

  let { items, children, num = 3, getAspectRatio }: MasonryProps<T> = $props();

  // Distribute items across columns by always appending to the column with
  // the smallest accumulated height, using each item's aspect ratio (from
  // picture resolution metadata when available) to estimate the height it
  // will take up at a fixed column width. This keeps columns balanced
  // without waiting for images to load and reflow.
  let columns: T[][] = $derived.by(() => {
    const cols: T[][] = Array.from({ length: num }, () => []);
    const heights = new Array(num).fill(0);
    for (const item of items) {
      const ratio = getAspectRatio?.(item) || DEFAULT_ASPECT_RATIO;
      let shortest = 0;
      for (let i = 1; i < num; i++) {
        if (heights[i] < heights[shortest]) shortest = i;
      }
      cols[shortest].push(item);
      heights[shortest] += 1 / ratio;
    }
    return cols;
  });
</script>

<div class="masonry">
  {#each columns as column}
    <div class="masonry-column">
      {#each column as item}
        {@render children(item)}
      {/each}
    </div>
  {/each}
</div>

<style>
  .masonry {
    flex: 1;
    display: flex;
    flex-direction: row;
    gap: 6px;
  }

  .masonry-column {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
</style>
