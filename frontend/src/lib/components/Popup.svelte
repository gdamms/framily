<script lang="ts">
  import { onMount, type Snippet } from "svelte";

  interface Props {
    children: Snippet;
    isOpen?: boolean;
    onClose?: () => void;
  }

  let { children, isOpen = $bindable(false), onClose = () => {} }: Props = $props();

  function close() {
    isOpen = false;
    onClose();
  }

  function handleBackgroundClick(event: MouseEvent): void {
    if (event.target === event.currentTarget) {
      close();
    }
  }

  function handleEscapeKey(event: KeyboardEvent): void {
    if (event.key === "Escape") {
      close();
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

<div
  class="popup"
  class:isOpen
  onclick={handleBackgroundClick}
  onkeypress={() => {}}
  role="button"
  tabindex="0"
>
  <div class="popup-content">
    {@render children()}
  </div>
</div>

<style>
  .popup {
    display: none;
    position: fixed;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background-color: rgba(0, 0, 0, 0.5);
    justify-content: center;
    align-items: center;
    z-index: 1000;
  }

  .popup.isOpen {
    display: flex;
  }

  .popup-content {
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    max-width: max(500px, 90%);
    max-height: 80%;
  }
</style>
