<script lang="ts">
  import { tick } from "svelte";
  import { api, type UserInfo } from "$lib/api";
  import { authStore } from "$lib/stores/auth";
  import { authView } from "$lib/app";
  import { overlay } from "$lib/overlay";
  import ConfirmPopup from "$lib/popups/ConfirmPopup.svelte";
  import Button from "$lib/ui/Button.svelte";
  import PasswordField from "$lib/ui/form/PasswordField.svelte";
  import ThemeToggle from "$lib/ui/ThemeToggle.svelte";
  import { themeStore, type ThemePreference } from "$lib/stores/theme";
  import { formatDate } from "$lib/date";
  import Pencil from "@lucide/svelte/icons/pencil";

  interface Props {
    user: UserInfo;
    onChanged?: () => void;
  }

  let { user, onChanged }: Props = $props();

  const preference = themeStore.preference;
  const THEME_OPTIONS: { id: ThemePreference; label: string }[] = [
    { id: "system", label: "System" },
    { id: "light", label: "Light" },
    { id: "dark", label: "Dark" },
  ];

  let editingName = $state(false);
  let nameDraft = $state("");
  let nameInputEl: HTMLInputElement | undefined = $state();

  function startEditingName() {
    nameDraft = user.display_name;
    editingName = true;
    tick().then(() => nameInputEl?.focus());
  }

  async function saveName() {
    if (!editingName) return;
    editingName = false;
    const trimmed = nameDraft.trim();
    if (!trimmed || trimmed === user.display_name) return;
    await api.user.updateProfile({ display_name: trimmed });
    onChanged?.();
  }

  function handleNameKeydown(event: KeyboardEvent) {
    if (event.key === "Enter") {
      event.preventDefault();
      (event.target as HTMLInputElement).blur();
    } else if (event.key === "Escape") {
      editingName = false;
    }
  }

  let currentPassword = $state("");
  let newPassword = $state("");
  let confirmNewPassword = $state("");
  let passwordError = $state("");
  let passwordSuccess = $state("");
  let changingPassword = $state(false);

  async function changePassword() {
    passwordError = "";
    passwordSuccess = "";

    if (!currentPassword || !newPassword || !confirmNewPassword) {
      passwordError = "All fields are required";
      return;
    }
    if (newPassword.length < 8) {
      passwordError = "New password must be at least 8 characters";
      return;
    }
    if (newPassword !== confirmNewPassword) {
      passwordError = "New passwords do not match";
      return;
    }

    changingPassword = true;
    try {
      await api.user.changePassword(currentPassword, newPassword);
      passwordSuccess = "Password changed";
      currentPassword = "";
      newPassword = "";
      confirmNewPassword = "";
    } catch (e: any) {
      passwordError = e.message || "Failed to change password";
    } finally {
      changingPassword = false;
    }
  }

  let deletePassword = $state("");
  let deleteError = $state("");
  let deletingAccount = $state(false);

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
</script>

<div class="settings-page">
  <h2 class="page-title">Settings</h2>

  <section class="section">
    <h3 class="section-title">Profile</h3>
    <div class="setting">
      <div class="setting-label">Display name</div>
      {#if editingName}
        <input
          class="name-input"
          bind:value={nameDraft}
          bind:this={nameInputEl}
          onblur={saveName}
          onkeydown={handleNameKeydown}
        />
      {:else}
        <button class="name-value editable" onclick={startEditingName}>
          <span>{user.display_name}</span>
          <Pencil size={14} />
        </button>
      {/if}
    </div>
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
        <div class="setting-value">{formatDate(user.created_at)}</div>
      </div>
    {/if}
  </section>

  <section class="section">
    <h3 class="section-title">Password</h3>
    <div class="setting">
      {#if passwordError}
        <p class="error">{passwordError}</p>
      {/if}
      {#if passwordSuccess}
        <p class="success">{passwordSuccess}</p>
      {/if}
      <div class="password-form">
        <PasswordField bind:value={currentPassword} placeholder="Current password" />
        <PasswordField bind:value={newPassword} placeholder="New password" />
        <PasswordField bind:value={confirmNewPassword} placeholder="Confirm new password" />
      </div>
      <Button
        variant="secondary"
        class="change-password-button"
        disabled={changingPassword}
        onclick={changePassword}
      >
        Change password
      </Button>
    </div>
  </section>

  <section class="section">
    <h3 class="section-title">Appearance</h3>
    <div class="setting">
      <div class="setting-label">Theme</div>
      <div class="theme-row">
        <div class="theme-options">
          {#each THEME_OPTIONS as option (option.id)}
            <button
              class="theme-option"
              class:selected={$preference === option.id}
              onclick={() => themeStore.setPreference(option.id)}
            >
              {option.label}
            </button>
          {/each}
        </div>
        <ThemeToggle />
      </div>
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
      <button class="delete-button" disabled={deletingAccount} onclick={startDeleteAccount}>
        Delete account
      </button>
    </div>
  </section>
</div>

<style>
  .settings-page {
    display: flex;
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
    overflow-y: auto;
  }

  .page-title {
    margin: 0;
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
    color: var(--color-text-secondary);
  }

  .danger-zone .section-title {
    color: var(--color-danger);
  }

  .setting {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    background: var(--color-bg-surface);
    padding: 1rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px var(--color-shadow);
  }

  .setting-label {
    font-weight: bold;
  }

  .setting-value {
    color: var(--color-text);
  }

  .setting-description {
    color: var(--color-text-secondary);
    font-size: 0.85rem;
    margin: -0.25rem 0 0;
  }

  .name-value {
    display: flex;
    align-items: center;
    gap: 0.4rem;
    background: none;
    border: none;
    padding: 0;
    cursor: pointer;
    color: var(--color-text);
    font: inherit;
    width: fit-content;
  }

  .name-input {
    font: inherit;
    border: none;
    border-bottom: 2px solid var(--color-text);
    background: none;
    color: var(--color-text);
    padding: 0;
    max-width: 100%;
  }

  .password-form {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
  }

  :global(.change-password-button) {
    align-self: flex-start;
  }

  .theme-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    flex-wrap: wrap;
  }

  .theme-options {
    display: flex;
    gap: 0.4rem;
  }

  .theme-option {
    border: 1px solid var(--color-border);
    background: var(--color-bg-surface);
    color: var(--color-text);
    padding: 0.4rem 0.75rem;
    border-radius: 999px;
    cursor: pointer;
    font: inherit;
    font-size: 0.85rem;
  }

  .theme-option.selected {
    background: var(--color-primary);
    border-color: var(--color-primary);
    color: var(--color-text-inverse);
  }

  .error {
    color: var(--color-danger);
    margin: 0;
  }

  .success {
    color: var(--color-success);
    margin: 0;
  }

  .delete-button {
    align-self: flex-start;
    background-color: var(--color-danger);
    color: var(--color-text-inverse);
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
