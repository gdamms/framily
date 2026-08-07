<script lang="ts">
  import { tick } from "svelte";
  import { api, type UserInfo, type UserFramilyInfo } from "$lib/api";
  import Galery from "$lib/components/Galery.svelte";
  import Framilies from "$lib/pages/framilies/Framilies.svelte";
  import Avatar from "$lib/ui/Avatar.svelte";
  import PageLayout from "$lib/ui/PageLayout.svelte";
  import LoadingPage from "$lib/ui/LoadingPage.svelte";
  import UploadPopup from "$lib/popups/UploadPopup.svelte";
  import { overlay } from "$lib/overlay";
  import Pencil from "@lucide/svelte/icons/pencil";
  import ImagePlus from "@lucide/svelte/icons/image-plus";

  interface Props {
    username: string;
    currentUsername: string;
    myFramilies: UserFramilyInfo[];
  }

  let { username, currentUsername, myFramilies }: Props = $props();

  let isOwnProfile = $derived(username === currentUsername);

  let user: UserInfo | undefined = $state();
  let pictures = $derived(user?.pictures ?? []);
  let framilies = $derived(user?.framilies ?? []);
  type View = "pictures" | "framilies";
  let view: View = $state("pictures");

  const TABS = [
    { id: "pictures" as const, label: "Pictures" },
    { id: "framilies" as const, label: "Framilies" },
  ];

  function openUploadPopup() {
    overlay.open(UploadPopup, {
      framilies,
      framilyCodes: framilies.map((f) => f.code),
      onUploaded: loadUser,
    });
  }

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

  async function loadUser() {
    const response = await api.user.getInfo(username);
    user = response.user;
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
  <LoadingPage />
{:else}
  {#snippet header()}
    <div class="profile-header">
      <Avatar kind="user" id={user!.username} label={user!.display_name} editable={isOwnProfile} size={64} />
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
            <span>{user!.display_name}</span>
            <Pencil size={16} />
          </button>
        {:else}
          <div class="profile-name">{user!.display_name}</div>
        {/if}
        <div class="profile-username">@{user!.username}</div>
      </div>
    </div>
  {/snippet}

  {#snippet content()}
    {#if view === "pictures"}
      {#if isOwnProfile}
        <button class="add-picture" onclick={openUploadPopup}>
          <ImagePlus size={16} />
          Add picture
        </button>
      {/if}
      <Galery {pictures} {currentUsername} {myFramilies} onPictureChanged={loadUser} />
    {:else if view === "framilies"}
      <Framilies {framilies} onFramilyChanged={loadUser} />
    {/if}
  {/snippet}

  <PageLayout {header} tabs={TABS} selected={view} onSelect={(id) => (view = id)} {content} />
{/if}

<style>
  .profile-header {
    background: var(--color-bg-page);
    padding: 0 1rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
    width: 100%;
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
    border-bottom: 2px solid var(--color-text);
    background: none;
    color: var(--color-text);
    padding: 0;
    max-width: 100%;
  }

  .profile-username {
    font-size: 14px;
    color: var(--color-text-secondary);
  }

  .add-picture {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    align-self: flex-start;
    background-color: var(--color-success);
    color: var(--color-text-inverse);
    border: none;
    border-radius: 6px;
    padding: 0.5rem 1rem;
    cursor: pointer;
    margin: 0 1rem;
  }
</style>
