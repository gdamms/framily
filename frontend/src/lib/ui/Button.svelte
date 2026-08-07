<script lang="ts">
  import type { Snippet } from "svelte";

  interface Props {
    children: Snippet;
    onclick?: () => void;
    type?: "button" | "submit" | "reset";
    variant?: "primary" | "secondary" | "danger" | "ghost";
    disabled?: boolean;
    class?: string;
  }

  let {
    children,
    onclick,
    type = "button",
    variant = "primary",
    disabled = false,
    class: _class = "",
  }: Props = $props();
</script>

<button class="btn btn-{variant} {_class}" {onclick} {type} {disabled}>
  {@render children()}
</button>

<style>
  .btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    border: none;
    border-radius: 8px;
    padding: 0.65rem 1.25rem;
    font: inherit;
    font-weight: 600;
    color: inherit;
    cursor: pointer;
    transition: background-color 0.15s ease, transform 0.05s ease;
  }

  .btn:active:not(:disabled) {
    transform: scale(0.97);
  }

  .btn:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .btn-primary {
    background-color: var(--color-primary);
    color: var(--color-text-inverse);
  }

  .btn-primary:hover:not(:disabled) {
    background-color: var(--color-primary-hover);
  }

  .btn-secondary {
    background-color: var(--color-bg-secondary);
    color: var(--color-text);
  }

  .btn-secondary:hover:not(:disabled) {
    background-color: var(--color-bg-secondary-hover);
  }

  .btn-danger {
    background-color: var(--color-danger);
    color: var(--color-text-inverse);
  }

  .btn-danger:hover:not(:disabled) {
    background-color: var(--color-danger-hover);
  }

  .btn-ghost {
    background-color: transparent;
  }

  .btn-ghost:hover:not(:disabled) {
    background-color: var(--color-bg-hover);
  }
</style>
