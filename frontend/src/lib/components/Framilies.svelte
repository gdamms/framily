<script lang="ts">
  import { type FramilyInfo, type FramilyListItem } from "$lib/api";
  import FramiliesItem from "./FramiliesItem.svelte";

  interface Props {
    framilies: FramilyInfo[] | FramilyListItem[];
  }

  let { framilies }: Props = $props();
</script>

<div class="framilies">
  {#each framilies as framily}
    <FramiliesItem {framily} />
  {/each}
</div>

<style>
  .framilies {
    display: flex;
    flex-direction: column;
    padding: 1rem;
    gap: 1rem;
  }
</style>
