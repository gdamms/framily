<script lang="ts">
  import { tick } from "svelte";
  import { goto } from "$app/navigation";
  import { api, type UserInfo } from "$lib/api";
  import { authStore } from "$lib/stores/auth";
  import Galery from "./Galery.svelte";
  import Framilies from "./Framilies.svelte";
  import Avatar from "./Avatar.svelte";
  import ConfirmPopup from "./ConfirmPopup.svelte";
  import PasswordField from "./PasswordField.svelte";
  import { formatDate } from "$lib/date";
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

  let deletePassword = $state("");
  let deleteError = $state("");
  let deleteConfirmOpen = $state(false);
  let deletingAccount = $state(false);

  function startDeleteAccount() {
    deleteError = "";
    if (!deletePassword) {
      deleteError = "Enter your password to confirm.";
      return;
    }
    deleteConfirmOpen = true;
  }

  async function deleteAccount() {
    deleteError = "";
    deletingAccount = true;
    try {
      await api.user.deleteAccount(deletePassword);
      authStore.clearToken();
      await goto("/login");
    } catch (e: any) {
      deleteError = e.message || "Failed to delete account";
    } finally {
      deletingAccount = false;
      deletePassword = "";
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
      <Avatar kind="user" id={user.username} label={user.display_name} editable={isOwnProfile} size={64} />
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
        <ConfirmPopup
          bind:isOpen={deleteConfirmOpen}
          prompt="Delete your account? This cannot be undone."
          onConfirm={deleteAccount}
        />
        <div class="settings">
          <section class="section">
            <h3 class="section-title">Account</h3>
            <div class="setting">
              <div class="setting-label">Username</div>
              <div class="setting-value">@{user.username}</div>
            </div>
            {#if user.email}
              <div class="setting">
                <div class="setting-label">Email</div>
                <div class="setting-value">{user.email}</div>
              </div>
            {/if}
            {#if user.created_at}
              <div class="setting">
                <div class="setting-label">Member since</div>
                <div class="setting-value">
                  {formatDate(user.created_at)}
                </div>
              </div>
            {/if}
          </section>

          <section class="section danger-zone">
            <h3 class="section-title">Danger zone</h3>

            {#if deleteError}
              <p class="error">{deleteError}</p>
            {/if}

            <div class="setting">
              <div class="setting-label">Delete account</div>
              <div class="setting-description">
                Permanently deletes your account. Your uploaded pictures stay in
                shared framilies but are no longer attributed to you.
              </div>
              <PasswordField bind:value={deletePassword} />
              <button
                class="delete-button"
                disabled={deletingAccount}
                onclick={startDeleteAccount}
              >
                Delete account
              </button>
            </div>
          </section>
        </div>
      {/if}
    </div>
  </div>
{/if}

<style>
  .profile {
    flex: 1;
    min-height: 0;
    display: flex;
    flex-direction: column;
    overflow: hidden;
  }

  .profile-header {
    background: #eee;
    padding: 0 1rem;
    display: flex;
    align-items: center;
    gap: 1rem;
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
    flex: 1;
    min-height: 0;
    overflow-y: auto;
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

  .settings {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
  }

  .section {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }

  .section-title {
    margin: 0;
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 0.03em;
    color: #666;
  }

  .danger-zone .section-title {
    color: #dc3545;
  }

  .setting {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    background: white;
    padding: 1rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .setting-label {
    font-weight: bold;
  }

  .setting-value {
    color: #333;
  }

  .setting-description {
    color: #666;
    font-size: 0.85rem;
    margin: -0.25rem 0 0;
  }

  .error {
    color: #dc3545;
    margin: 0;
  }

  .delete-button {
    align-self: flex-start;
    background-color: #dc3545;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 0.5rem 1rem;
    cursor: pointer;
  }

  .delete-button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
</style>
