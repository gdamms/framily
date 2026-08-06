<script lang="ts" generics="T extends string">
  import type { Snippet } from "svelte";
  import TabBar from "./TabBar.svelte";

  interface Tab<T> {
    id: T;
    label: string;
  }

  interface Props<T> {
    header: Snippet;
    tabs: Tab<T>[];
    selected: T;
    onSelect: (id: T) => void;
    content: Snippet;
  }

  let { header, tabs, selected, onSelect, content }: Props<T> = $props();
</script>

<div class="page-layout">
  <div class="page-header">
    {@render header()}
  </div>
  <TabBar {tabs} {selected} {onSelect} />
  <div class="page-content">
    {@render content()}
  </div>
</div>

<style>
  .page-layout {
    flex: 1;
    min-height: 0;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .page-header {
    height: 5rem;
    width: 100%;
    display: flex;
    justify-content: center;
    align-items: center;
  }

  .page-content {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
</style>
