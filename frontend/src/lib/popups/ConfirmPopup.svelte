<script lang="ts">
  import { m } from "$lib/i18n.svelte";
  import Button from "$lib/ui/Button.svelte";

  interface Props {
    prompt?: string;
    onCancel?: () => void;
    onConfirm?: () => void;
    close?: () => void;
  }

  let {
    prompt,
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
  <p>{prompt ?? m.common_are_you_sure()}</p>
  <div class="buttons">
    <Button variant="secondary" onclick={cancel}>{m.common_cancel()}</Button>
    <Button variant="primary" onclick={confirm}>{m.common_confirm()}</Button>
  </div>
</div>

<style>
  .confirm-popup {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
    background: var(--color-bg-surface);
    color: var(--color-text);
    padding: 1.5rem;
    border-radius: 10px;
  }

  .buttons {
    display: flex;
    gap: 1rem;
  }
</style>
