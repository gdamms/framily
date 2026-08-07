<script lang="ts">
  import { overlay } from "$lib/overlay";

  const stack = overlay.stack;

  function handleBackdropClick(event: MouseEvent, id: number) {
    if (event.target === event.currentTarget) {
      overlay.close(id);
    }
  }

  function handleKeydown(event: KeyboardEvent) {
    if (event.key === "Escape") {
      overlay.closeTop();
    }
  }
</script>

<svelte:window onkeydown={handleKeydown} />

{#each $stack as entry (entry.id)}
  <div
    class="backdrop"
    onclick={(event) => handleBackdropClick(event, entry.id)}
    onkeypress={() => {}}
    role="presentation"
  >
    <div class="card">
      <entry.component {...entry.props} close={() => overlay.close(entry.id)} />
    </div>
  </div>
{/each}

<style>
  .backdrop {
    position: fixed;
    inset: 0;
    background-color: var(--color-overlay-backdrop);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
    padding: 1rem;
    box-sizing: border-box;
  }

  .card {
    max-width: max(500px, 90%);
    max-height: 80%;
    overflow: auto;
  }
</style>
