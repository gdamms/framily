<script lang="ts">
  import Popup from "$lib/components/Popup.svelte";
  import Button from "$lib/components/Button.svelte";

  interface Props {
    prompt?: string;
    isOpen?: boolean;
    onCancel?: () => void;
    onConfirm?: () => void;
  }

  let {
    prompt = "Are you sure?",
    isOpen = $bindable(false),
    onCancel = () => {},
    onConfirm = () => {},
  }: Props = $props();

  async function cancel() {
    isOpen = false;
    onCancel();
  }

  async function confirm() {
    isOpen = false;
    onConfirm();
  }

  async function onClose() {
    onCancel();
  }
</script>

<Popup bind:isOpen {onClose}>
  <div class="confirm-popup">
    <p>{prompt}</p>
    <div class="buttons">
      <Button onclick={cancel} color="#b8d9f2">Cancel</Button>
      <Button onclick={confirm}>Confirm</Button>
    </div>
  </div>
</Popup>

<style>
  .confirm-popup {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
  }

  .buttons {
    display: flex;
    gap: 1rem;
  }
</style>
