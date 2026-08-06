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
    background-color: #c8dadf;
    color: #333;
  }

  .status-error {
    background-color: #e74c3c;
    color: white;
  }

  .status-success {
    background-color: #2ecc71;
    color: white;
  }
</style>
