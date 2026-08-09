<script lang="ts">
  import StatusMessage from "./StatusMessage.svelte";
  import Button from "./Button.svelte";

  interface Props {
    message?: string;
    onRetry?: () => void;
    onBack?: () => void;
    backLabel?: string;
  }

  let {
    message = "Something went wrong.",
    onRetry,
    onBack,
    backLabel = "Back to dashboard",
  }: Props = $props();
</script>

<div class="error-page">
  <StatusMessage text={message} type="error" />
  <div class="error-actions">
    {#if onRetry}
      <Button variant="secondary" onclick={onRetry}>Try again</Button>
    {/if}
    {#if onBack}
      <Button onclick={onBack}>{backLabel}</Button>
    {/if}
  </div>
</div>

<style>
  .error-page {
    flex: 1;
    min-height: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    gap: 1rem;
    padding: 1rem;
  }

  .error-actions {
    display: flex;
    gap: 0.75rem;
  }
</style>
