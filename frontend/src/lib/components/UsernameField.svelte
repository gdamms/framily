<script lang="ts">
  import TextField from "$lib/components/TextField.svelte";

  interface Props {
    value?: string;
    placeholder?: string;
  }

  let {
    value = $bindable(""),
    placeholder = "Enter your username"
  }: Props = $props();
</script>

<TextField type="text" {placeholder} bind:value required />
