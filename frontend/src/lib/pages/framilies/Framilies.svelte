<script lang="ts">
  import { type UserFramilyInfo } from "$lib/api";
  import FramiliesItem from "./FramiliesItem.svelte";
  import ListPlus from "@lucide/svelte/icons/list-plus";

  interface Props {
    framilies: UserFramilyInfo[];
    onAddFramily?: () => void;
    onFramilyChanged?: () => void;
  }

  let { framilies, onAddFramily, onFramilyChanged }: Props = $props();
</script>

<div class="framilies">
  {#if onAddFramily}
    <button class="add-framily" onclick={onAddFramily}>
      <ListPlus size={16} />
      Add framily
    </button>
  {/if}
  {#each framilies as framily}
    <FramiliesItem {framily} onChanged={onFramilyChanged} />
  {/each}
</div>

<style>
  .framilies {
    display: flex;
    flex-direction: column;
    padding: 1rem;
    gap: 1rem;
  }

  .add-framily {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    align-self: flex-start;
    background-color: #28a745;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 0.5rem 1rem;
    cursor: pointer;
  }
</style>
