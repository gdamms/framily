<script lang="ts">
  import { type FramilyMember } from "$lib/api";
  import { app } from "$lib/app";

  interface Props {
    members: FramilyMember[];
  }

  let { members }: Props = $props();
</script>

<div class="members-list">
  {#each members as member}
    <button
      class="member"
      onclick={() =>
        app.navigate({ page: "profile", username: member.username, section: "pictures" })}
    >
      <div class="member-name">{member.display_name}</div>
      <div class="member-username">@{member.username}</div>
    </button>
  {/each}
</div>

<style>
  .members-list {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
  }

  .member {
    border: none;
    text-align: left;
    background: white;
    padding: 1rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .member-name {
    font-weight: bold;
    font-size: 1.2rem;
  }

  .member-username {
    color: #666;
  }
</style>
