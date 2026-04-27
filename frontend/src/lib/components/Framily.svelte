<script lang="ts">
  import { onMount } from "svelte";
  import { api, type FramilyInfo, type PictureInfo } from "$lib/api";
  import Galery from "./Galery.svelte";

  interface Props {
    framily: FramilyInfo;
  }

  let { framily }: Props = $props();

  let pictures: PictureInfo[] = $state([]);

  type View = "pictures" | "members" | "settings";
  let view: View = $state("pictures");

  onMount(async () => {
    let infoResponse = await api.framily.info(framily.code);
    framily = infoResponse.framily;

    let picResponse = await api.pictures.list({
      framily_code: framily.code,
    });
    pictures = picResponse.pictures;
  });
</script>

<div class="framily-page">
  <div class="framily-header">
    <div class="framily-name">{framily.name}</div>
    <div class="framily-code">@{framily.code}</div>
  </div>
  <div class="framily-nav">
    <button
      class="button"
      class:selected={view === "pictures"}
      onclick={() => (view = "pictures")}
    >
      Pictures
    </button>
    <button
      class="button"
      class:selected={view === "members"}
      onclick={() => (view = "members")}
    >
      Members
    </button>
    <button
      class="button"
      class:selected={view === "settings"}
      onclick={() => (view = "settings")}
    >
      Settings
    </button>
  </div>
  <div class="framily-content">
    {#if view === "pictures"}
      <Galery {pictures} />
    {:else if view === "members"}
      <div class="members-list">
        {#each framily.members as member}
          <button class="member">
            <div class="member-name">{member.display_name}</div>
            <div class="member-username">@{member.username}</div>
          </button>
        {/each}
      </div>
    {:else if view === "settings"}
      <div class="settings">
        <h3>Settings</h3>
        <p>This is where you can manage your framily settings.</p>
      </div>
    {/if}
  </div>
</div>

<style>
  .framily-page {
    flex: 1;
    display: flex;
    flex-direction: column;
    height: 100%;
  }

  .framily-header {
    background: #eee;
    padding: 0 1rem;
  }

  .framily-name {
    font-size: 24px;
    font-weight: bold;
  }

  .framily-code {
    font-size: 14px;
    color: #666;
  }

  .framily-nav {
    display: flex;
    flex-direction: row;
    padding: 0.5rem 0;
  }

  .button {
    background: none;
    border: none;
    padding: 0.5rem 1rem;
    cursor: pointer;
    flex: 1;
  }

  .button.selected {
    font-weight: bold;
    border-bottom: 2px solid #333;
  }

  .framily-content {
    flex: 1;
  }

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
