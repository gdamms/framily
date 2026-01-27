<script lang="ts">
  import Tag from "./Tag.svelte";

  interface Props {
    username: string;
    displayName: string;
  }

  let { username, displayName }: Props = $props();
</script>

<Tag href="/profile/{username}" color="#007BFF">
  {displayName}
</Tag>
