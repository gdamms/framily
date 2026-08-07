<script lang="ts">
  interface Props {
    text?: string;
    type?: "info" | "error" | "success";
  }

  let { text, type = "info" }: Props = $props();
</script>

{#if text}
  <div class="status status-{type}">{text}</div>
{/if}

<style>
  .status {
    padding: 0.6rem 1rem;
    border-radius: 6px;
    text-align: center;
    font-weight: 600;
  }

  .status-info {
    background-color: var(--color-dropzone-bg);
    color: var(--color-text);
  }

  .status-error {
    background-color: var(--color-status-error-bg);
    color: var(--color-text-inverse);
  }

  .status-success {
    background-color: var(--color-status-success-bg);
    color: var(--color-text-inverse);
  }
</style>
