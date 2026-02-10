<script lang="ts">
  import { onMount, type Snippet } from "svelte";

  interface Props {
    children: Snippet;
    onClose?: () => void;
  }

  let { children, onClose }: Props = $props();

  function handleBackgroundClick(event: MouseEvent): void {
    if (event.target === event.currentTarget && onClose) {
      onClose();
    }
  }

  function handleEscapeKey(event: KeyboardEvent): void {
    if (event.key === "Escape" && onClose) {
      onClose();
    }
  }

  // Add event listener for Escape key when the component is mounted
  onMount(() => {
    window.addEventListener("keydown", handleEscapeKey);
    return () => {
      window.removeEventListener("keydown", handleEscapeKey);
    };
  });
</script>

<button class="popup" onclick={handleBackgroundClick}>
  <div class="popup-content">
    {@render children()}
  </div>
</button>

<style>
  .popup {
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
  }

  .popup-content {
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    max-width: max(500px, 90%);
    max-height: 80%;
  }
</style>
