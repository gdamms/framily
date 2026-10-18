<script lang="ts">
  import type { Snippet } from "svelte";

  interface Props {
    children?: Snippet;
    title?: string;
    errorMessage?: string;
    submitHandler?: () => void;
  }

  let {
    children,
    title = "",
    errorMessage = "",
    submitHandler = () => {},
  }: Props = $props();

  // Handle submission in JS only: a native submit would reload the SPA.
  function onsubmit(event: SubmitEvent) {
    event.preventDefault();
    submitHandler();
  }
</script>

<div class="form">
  <h2>{title}</h2>
  <form {onsubmit}>
    {#if children}
      {@render children()}
    {/if}
  </form>
  {#if errorMessage}
    <p class="error">{errorMessage}</p>
  {/if}
</div>

<style>
  .form {
    max-width: 400px;
    margin: 0 auto;
    padding: 2rem;
    border: 1px solid var(--color-border);
    border-radius: 8px;
    box-shadow: 0 2px 4px var(--color-shadow);
    background: var(--color-bg-surface);
    color: var(--color-text);
  }

  h2 {
    text-align: center;
    margin-bottom: 1.5rem;
  }

  form {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .error {
    color: var(--color-danger);
    text-align: center;
    margin-top: 1rem;
  }
</style>
