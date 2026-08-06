<script lang="ts" generics="T extends string">
  interface Tab<T> {
    id: T;
    label: string;
  }

  interface Props<T> {
    tabs: Tab<T>[];
    selected: T;
    onSelect: (id: T) => void;
  }

  let { tabs, selected, onSelect }: Props<T> = $props();
</script>

<div class="tab-bar" role="tablist">
  {#each tabs as tab (tab.id)}
    <button
      class="tab"
      class:selected={tab.id === selected}
      role="tab"
      aria-selected={tab.id === selected}
      onclick={() => onSelect(tab.id)}
    >
      {tab.label}
    </button>
  {/each}
</div>

<style>
  .tab-bar {
    display: flex;
    flex-direction: row;
    padding: 0.5rem 0;
  }

  .tab {
    background: none;
    border: none;
    padding: 0.5rem 1rem;
    cursor: pointer;
    flex: 1;
    font: inherit;
    color: inherit;
  }

  .tab.selected {
    font-weight: bold;
    border-bottom: 2px solid #333;
  }
</style>
