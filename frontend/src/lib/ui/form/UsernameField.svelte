<script lang="ts">
  import { m } from "$lib/i18n.svelte";
  import TextField from "./TextField.svelte";

  interface Props {
    value?: string;
    placeholder?: string;
  }

  let {
    value = $bindable(""),
    placeholder
  }: Props = $props();
</script>

<TextField type="text" placeholder={placeholder ?? m.field_username_placeholder()} bind:value required />
