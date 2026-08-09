<script lang="ts">
  import TextField from "./TextField.svelte";

  interface Props {
    value?: string;
    placeholder?: string;
  }

  let {
    value = $bindable(""),
    placeholder = "https://your-framily-server.example.com",
  }: Props = $props();
</script>

<TextField type="url" {placeholder} bind:value required />
