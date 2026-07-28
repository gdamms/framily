<script lang="ts">
  import { tick } from "svelte";
  import { api, type UserInfo } from "$lib/api";
  import Galery from "./Galery.svelte";
  import Framilies from "./Framilies.svelte";
  import Pencil from "@lucide/svelte/icons/pencil";
  import ImagePlus from "@lucide/svelte/icons/image-plus";

  interface Props {
    username: string;
    currentUsername: string;
    onAddPicture?: () => void;
  }

  let { username, currentUsername, onAddPicture }: Props = $props();

  let isOwnProfile = $derived(username === currentUsername);

  let user: UserInfo | undefined = $state();
  let pictures = $derived(user?.pictures ?? []);
  let framilies = $derived(user?.framilies ?? []);
  type View = "pictures" | "framilies" | "settings";
  let view: View = $state("pictures");

  let editingName = $state(false);
  let nameDraft = $state("");
  let nameInputEl: HTMLInputElement | undefined = $state();

  function startEditingName() {
    if (!isOwnProfile || !user) return;
    nameDraft = user.display_name;
    editingName = true;
    tick().then(() => nameInputEl?.focus());
  }

  async function saveName() {
    if (!editingName || !user) return;
    editingName = false;
    const trimmed = nameDraft.trim();
    if (!trimmed || trimmed === user.display_name) return;
    const response = await api.user.updateProfile({ display_name: trimmed });
    user = response.user;
  }

  function handleNameKeydown(event: KeyboardEvent) {
    if (event.key === "Enter") {
      event.preventDefault();
      (event.target as HTMLInputElement).blur();
    } else if (event.key === "Escape") {
      editingName = false;
    }
  }

  $effect(() => {
    // Re-fetch whenever `username` changes - this component instance is
    // reused across profile navigations (e.g. own profile -> a member's
    // profile -> own profile again), so onMount alone would only fetch once.
    const targetUsername = username;
    user = undefined;
    view = "pictures";
    api.user.getInfo(targetUsername).then((response) => {
      if (targetUsername === username) {
        user = response.user;
      }
    });
  });
</script>

{#if !user}
  <div class="profile">Loading...</div>
{:else}
  <div class="profile">
    <div class="profile-header">
      <div class="profile-avatar">Avatar</div>
      <div class="profile-names">
        {#if isOwnProfile && editingName}
          <input
            class="profile-name-input"
            bind:value={nameDraft}
            bind:this={nameInputEl}
            onblur={saveName}
            onkeydown={handleNameKeydown}
          />
        {:else if isOwnProfile}
          <button class="profile-name editable" onclick={startEditingName}>
            <span>{user.display_name}</span>
            <Pencil size={16} />
          </button>
        {:else}
          <div class="profile-name">{user.display_name}</div>
        {/if}
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
      {#if isOwnProfile}
        <button
          class="button"
          class:selected={view === "settings"}
          onclick={() => (view = "settings")}
        >
          Settings
        </button>
      {/if}
    </div>
    <div class="profile-content">
      {#if view === "pictures"}
        {#if isOwnProfile && onAddPicture}
          <button class="add-picture" onclick={onAddPicture}>
            <ImagePlus size={16} />
            Add picture
          </button>
        {/if}
        <Galery {pictures} />
      {:else if view === "framilies"}
        <Framilies {framilies} />
      {:else if view === "settings" && isOwnProfile}
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

  button.profile-name.editable {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    background: none;
    border: none;
    padding: 0;
    cursor: pointer;
    color: inherit;
    font-family: inherit;
  }

  .profile-name-input {
    font-size: 24px;
    font-weight: bold;
    font-family: inherit;
    border: none;
    border-bottom: 2px solid #333;
    background: none;
    padding: 0;
    max-width: 100%;
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

  .profile-content {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .add-picture {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    align-self: flex-start;
    background-color: #28a745;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 0.5rem 1rem;
    cursor: pointer;
    margin: 0 1rem;
  }
</style>
