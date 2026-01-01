<script lang="ts">
  interface Props {
    text: string;
    type?: "button" | "submit" | "reset" | null | undefined;
  }

  let { text = "", type = "button" }: Props = $props();
</script>

<button class="text-button" type={type}>{text}</button>

<style>
  .text-button {
    background-color: #007BFF;
    color: white;
    border: none;
    padding: 0.75rem;
    border-radius: 4px;
    font-size: 1rem;
    cursor: pointer;
  }

  .text-button:hover {
    background-color: #0056b3;
  }
</style>
