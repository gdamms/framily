<script lang="ts">
  import { tick } from "svelte";
  import { api, type UserInfo } from "$lib/api";
  import { authStore } from "$lib/stores/auth";
  import { authView } from "$lib/app";
  import { overlay } from "$lib/overlay";
  import Galery from "$lib/components/Galery.svelte";
  import Framilies from "$lib/pages/framilies/Framilies.svelte";
  import Avatar from "$lib/ui/Avatar.svelte";
  import PageLayout from "$lib/ui/PageLayout.svelte";
  import Button from "$lib/ui/Button.svelte";
  import ConfirmPopup from "$lib/popups/ConfirmPopup.svelte";
  import UploadPopup from "$lib/popups/UploadPopup.svelte";
  import PasswordField from "$lib/ui/form/PasswordField.svelte";
  import { formatDate } from "$lib/date";
  import Pencil from "@lucide/svelte/icons/pencil";
  import ImagePlus from "@lucide/svelte/icons/image-plus";
  import LogOut from "@lucide/svelte/icons/log-out";

  interface Props {
    username: string;
    currentUsername: string;
  }

  let { username, currentUsername }: Props = $props();

  let isOwnProfile = $derived(username === currentUsername);

  let user: UserInfo | undefined = $state();
  let pictures = $derived(user?.pictures ?? []);
  let framilies = $derived(user?.framilies ?? []);
  type View = "pictures" | "framilies" | "settings";
  let view: View = $state("pictures");

  const TABS = $derived(
    [
      { id: "pictures" as const, label: "Pictures" },
      { id: "framilies" as const, label: "Framilies" },
      ...(isOwnProfile ? [{ id: "settings" as const, label: "Settings" }] : []),
    ],
  );

  function openUploadPopup() {
    overlay.open(UploadPopup, { framilies, framilyCodes: framilies.map((f) => f.code) });
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

  let deletePassword = $state("");
  let deleteError = $state("");
  let deletingAccount = $state(false);

  function logout() {
    authStore.clearToken();
    authView.set("login");
  }

  function startDeleteAccount() {
    deleteError = "";
    if (!deletePassword) {
      deleteError = "Enter your password to confirm.";
      return;
    }
    overlay.open(ConfirmPopup, {
      prompt: "Delete your account? This cannot be undone.",
      onConfirm: deleteAccount,
    });
  }

  async function deleteAccount() {
    deleteError = "";
    deletingAccount = true;
    try {
      await api.user.deleteAccount(deletePassword);
      authStore.clearToken();
      authView.set("login");
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
  <div class="loading">Loading...</div>
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
      <Galery {pictures} />
    {:else if view === "framilies"}
      <Framilies {framilies} />
    {:else if view === "settings" && isOwnProfile}
      <div class="settings">
        <section class="section">
          <h3 class="section-title">Account</h3>
          <div class="setting">
            <div class="setting-label">Username</div>
            <div class="setting-value">@{user!.username}</div>
          </div>
          {#if user!.email}
            <div class="setting">
              <div class="setting-label">Email</div>
              <div class="setting-value">{user!.email}</div>
            </div>
          {/if}
          {#if user!.created_at}
            <div class="setting">
              <div class="setting-label">Member since</div>
              <div class="setting-value">
                {formatDate(user!.created_at)}
              </div>
            </div>
          {/if}
          <div class="setting">
            <div class="setting-label">Logout</div>
            <Button variant="secondary" class="logout-button" onclick={logout}>
              <LogOut size={16} />
              Logout
            </Button>
          </div>
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
  {/snippet}

  <PageLayout {header} tabs={TABS} selected={view} onSelect={(id) => (view = id)} {content} />
{/if}

<style>
  .loading {
    flex: 1;
    padding: 1rem;
  }

  .profile-header {
    background: #eee;
    padding: 0 1rem;
    display: flex;
    align-items: center;
    gap: 1rem;
    padding: 1rem;
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

  :global(.logout-button) {
    align-self: flex-start;
  }

  .delete-button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
</style>
