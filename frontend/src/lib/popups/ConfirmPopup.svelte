<script lang="ts">
  import Button from "$lib/ui/Button.svelte";

  interface Props {
    prompt?: string;
    onCancel?: () => void;
    onConfirm?: () => void;
    close?: () => void;
  }

  let {
    prompt = "Are you sure?",
    onCancel,
    onConfirm,
    close = () => {},
  }: Props = $props();

  function cancel() {
    onCancel?.();
    close();
  }

  function confirm() {
    onConfirm?.();
    close();
  }
</script>

<div class="confirm-popup">
  <p>{prompt}</p>
  <div class="buttons">
    <Button variant="secondary" onclick={cancel}>Cancel</Button>
    <Button variant="primary" onclick={confirm}>Confirm</Button>
  </div>
</div>

<style>
  .confirm-popup {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    background: white;
    padding: 1.5rem;
    border-radius: 10px;
  }

  .buttons {
    display: flex;
    gap: 1rem;
  }
</style>
