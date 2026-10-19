<script lang="ts">
  import { type UserFramilyInfo } from "$lib/api";
  import FramiliesItem from "./FramiliesItem.svelte";
  import ListPlus from "@lucide/svelte/icons/list-plus";
  import Bluetooth from "@lucide/svelte/icons/bluetooth";

  interface Props {
    framilies: UserFramilyInfo[];
    onAddFramily?: () => void;
    onSetupFrame?: () => void;
    onFramilyChanged?: () => void;
  }

  let { framilies, onAddFramily, onSetupFrame, onFramilyChanged }: Props = $props();
</script>

<div class="framilies">
  {#if onAddFramily || onSetupFrame}
    <div class="actions">
      {#if onAddFramily}
        <button class="add-framily" onclick={onAddFramily}>
          <ListPlus size={16} />
          Add framily
        </button>
      {/if}
      {#if onSetupFrame}
        <button class="add-framily" onclick={onSetupFrame}>
          <Bluetooth size={16} />
          Set up a frame
        </button>
      {/if}
    </div>
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

  .actions {
    display: flex;
    flex-wrap: wrap;
    gap: 0.75rem;
  }

  .add-framily {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    align-self: flex-start;
    background-color: var(--color-success);
    color: var(--color-text-inverse);
    border: none;
    border-radius: 6px;
    padding: 0.5rem 1rem;
    cursor: pointer;
  }
</style>
