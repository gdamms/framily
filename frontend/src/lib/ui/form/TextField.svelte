<script lang="ts">
  interface Props {
    value?: string;
    type?: string;
    placeholder?: string;
    required?: boolean;
  }

  let {
    value = $bindable(),
    type = "text",
    placeholder = "",
    required = false,
  }: Props = $props();
</script>

<input {type} bind:value {placeholder} {required} class="text-field" />

<style>
  .text-field {
    padding: 0.5rem;
    border: 0;
    border-bottom: 1px solid #ccc;
    border-radius: 4px;
    width: 100%;
    box-sizing: border-box;
  }
</style>
