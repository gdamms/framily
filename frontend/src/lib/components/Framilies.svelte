<script lang="ts">
  import { type FramilyInfo } from "$lib/api";
  interface Props {
    framilies: FramilyInfo[];
  }

  let { framilies }: Props = $props();
</script>

<div class="framilies">
  {#each framilies as framily}
    <button class="framily">
      <div class="framily-name">{framily.name}</div>
      <div class="framily-code">@{framily.code}</div>
    </button>
  {/each}
</div>

<style>
  .framilies {
    display: flex;
    flex-direction: column;
    padding: 1rem;
    gap: 1rem;
  }

  .framily {
    background: white;
    padding: 1rem;
    text-align: left;
    border: none;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .framily-name {
    font-weight: bold;
    font-size: 1.2rem;
  }

  .framily-code {
    color: #666;
  }
</style>
