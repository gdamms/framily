<script lang="ts">
  import TextField from "./TextField.svelte";

  interface Props {
    value?: string;
  }

  let { value = $bindable("") }: Props = $props();
</script>

<TextField type="password" placeholder="Enter your password" bind:value required />
