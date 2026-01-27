<script lang="ts">
  import Tag from "./Tag.svelte";

  interface Props {
    framilyCode: string;
    framilyName: string;
  }

  let { framilyCode, framilyName }: Props = $props();
</script>

<Tag href="/framily/{framilyCode}" color="#FF5733">
  {framilyName}
</Tag>
