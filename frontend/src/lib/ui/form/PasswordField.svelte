<script lang="ts">
  import TextField from "./TextField.svelte";

  interface Props {
    value?: string;
    placeholder?: string;
  }

  let { value = $bindable(""), placeholder = "Enter your password" }: Props = $props();
</script>

<TextField type="password" {placeholder} bind:value required />
