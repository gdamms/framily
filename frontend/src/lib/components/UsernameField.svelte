<script lang="ts">
  import TextField from "$lib/components/TextField.svelte";

  interface Props {
    value?: string;
  }

  let { value = $bindable("") }: Props = $props();
</script>

<TextField type="text" placeholder="Enter your username" bind:value required />
