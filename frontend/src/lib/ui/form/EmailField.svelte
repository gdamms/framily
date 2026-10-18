<script lang="ts">
  import { m } from "$lib/i18n.svelte";
  import TextField from "./TextField.svelte";

  interface Props {
    value?: string;
  }

  let { value = $bindable("") }: Props = $props();
</script>

<TextField type="email" placeholder={m.field_email_placeholder()} bind:value required />
