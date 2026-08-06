<script lang="ts">
  import TextField from "./TextField.svelte";

  interface Props {
    value?: string;
  }

  let { value = $bindable("") }: Props = $props();
</script>

<TextField type="email" placeholder="Enter your email" bind:value required />
