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
    background-color: #4593e7;
    color: white;
  }

  .btn-primary:hover:not(:disabled) {
    background-color: #327bcf;
  }

  .btn-secondary {
    background-color: #e2e8ec;
    color: #333;
  }

  .btn-secondary:hover:not(:disabled) {
    background-color: #d3dbe0;
  }

  .btn-danger {
    background-color: #dc3545;
    color: white;
  }

  .btn-danger:hover:not(:disabled) {
    background-color: #c22836;
  }

  .btn-ghost {
    background-color: transparent;
  }

  .btn-ghost:hover:not(:disabled) {
    background-color: rgba(0, 0, 0, 0.06);
  }
</style>
