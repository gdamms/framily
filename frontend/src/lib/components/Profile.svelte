<script lang="ts">
  import { onMount } from "svelte";
  import {
    api,
    type FramilyInfo,
    type FramilyListItem,
    type PictureInfo,
    type UserInfo,
  } from "$lib/api";
  import Galery from "./Galery.svelte";
  import Framilies from "./Framilies.svelte";

  interface Props {
    username: string;
  }

  let { username }: Props = $props();

  let user: UserInfo | undefined = $state();
  let pictures: PictureInfo[] = $state([]);
  let framilies: FramilyListItem[] = $state([]);
  type View = "pictures" | "framilies" | "settings";
  let view: View = $state("pictures");

  onMount(async () => {
    let response = await api.user.getInfo(username);
    user = response.user;

    let responsePic = await api.pictures.list({
      username: user.username,
    });
    pictures = responsePic.pictures;

    let responseFram = await api.framily.list(user.username);
    framilies = responseFram.framilies;
  });
</script>

{#if !user}
  <div class="profile">Loading...</div>
{:else}
  <div class="profile">
    <div class="profile-header">
      <div class="profile-avatar">Avatar</div>
      <div class="profile-names">
        <div class="profile-name">{user.display_name}</div>
        <div class="profile-username">@{user.username}</div>
      </div>
    </div>
    <div class="profile-nav">
      <button
        class="button"
        class:selected={view === "pictures"}
        onclick={() => (view = "pictures")}
      >
        Pictures
      </button>
      <button
        class="button"
        class:selected={view === "framilies"}
        onclick={() => (view = "framilies")}
      >
        Framilies
      </button>
      <button
        class="button"
        class:selected={view === "settings"}
        onclick={() => (view = "settings")}
      >
        Settings
      </button>
    </div>
    <div class="profile-content">
      {#if view === "pictures"}
        <Galery {pictures} />
      {:else if view === "framilies"}
        <Framilies {framilies} />
      {:else if view === "settings"}
        <div class="settings">Settings content goes here</div>
      {/if}
    </div>
  </div>
{/if}

<style>
  .profile-header {
    background: #eee;
    padding: 0 1rem;
    display: flex;
    align-items: center;
    gap: 1rem;
  }

  .profile-avatar {
    width: 64px;
    height: 64px;
    background: #ccc;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .profile-name {
    font-size: 24px;
    font-weight: bold;
  }

  .profile-username {
    font-size: 14px;
    color: #666;
  }

  .profile-nav {
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
    border-bottom: 2px solid #333;
    font-weight: bold;
  }
</style>
