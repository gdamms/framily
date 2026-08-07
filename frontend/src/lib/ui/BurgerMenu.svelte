<script lang="ts">
  import { app } from "$lib/app";
  import { authStore } from "$lib/stores/auth";
  import { authView } from "$lib/app";
  import ThemeToggle from "./ThemeToggle.svelte";
  import Menu from "@lucide/svelte/icons/menu";
  import UserRound from "@lucide/svelte/icons/user-round";
  import Settings from "@lucide/svelte/icons/settings";
  import LogOut from "@lucide/svelte/icons/log-out";
  import { themeStore } from "$lib/stores/theme";

  interface Props {
    currentUsername: string;
  }

  let { currentUsername }: Props = $props();

  let open = $state(false);
  let containerEl: HTMLDivElement | undefined = $state();

  function close() {
    open = false;
  }

  function toggle() {
    open = !open;
  }

  function goProfile() {
    app.navigate({ page: "profile", username: currentUsername, section: "pictures" });
    close();
  }

  function goSettings() {
    app.navigate({ page: "settings" });
    close();
  }

  function logout() {
    close();
    authStore.clearToken();
    authView.set("login");
  }

  function handleWindowClick(event: MouseEvent) {
    if (open && containerEl && !containerEl.contains(event.target as Node)) {
      close();
    }
  }

  function handleKeydown(event: KeyboardEvent) {
    if (open && event.key === "Escape") {
      close();
    }
  }

  function cycleTheme() {
    themeStore.cycle();
  }
</script>

<svelte:window onclick={handleWindowClick} onkeydown={handleKeydown} />

<div class="burger-menu" bind:this={containerEl}>
  <button class="trigger" type="button" onclick={toggle} aria-label="Menu" aria-expanded={open}>
    <Menu size={22} />
  </button>

  {#if open}
    <div class="dropdown" role="menu">
      <button class="item" role="menuitem" onclick={goProfile}>
        <UserRound size={18} />
        Profile
      </button>
      <button class="item" role="menuitem" onclick={goSettings}>
        <Settings size={18} />
        Settings
      </button>
      <button class="item theme-item" onclick={cycleTheme} role="menuitem">
        <div class="theme-toggle-container">
          <ThemeToggle size={18} />
        </div>
        <span class="theme-label">Theme</span>
      </button>
      <button class="item danger" role="menuitem" onclick={logout}>
        <LogOut size={18} />
        Logout
      </button>
    </div>
  {/if}
</div>

<style>
  .burger-menu {
    position: relative;
  }

  .trigger {
    display: flex;
    align-items: center;
    justify-content: center;
    border: none;
    border-radius: 999px;
    padding: 0.5rem;
    background: transparent;
    color: var(--color-text);
    cursor: pointer;
  }

  .trigger:hover {
    background-color: var(--color-bg-hover);
  }

  .dropdown {
    position: absolute;
    top: calc(100% + 0.5rem);
    right: 0;
    display: flex;
    flex-direction: column;
    min-width: 12rem;
    background: var(--color-bg-surface);
    border-radius: 10px;
    box-shadow: 0 4px 12px var(--color-shadow);
    padding: 0.4rem;
    gap: 0.15rem;
    z-index: 20;
  }

  .item {
    display: flex;
    align-items: center;
    gap: 1rem;
    border: none;
    background: none;
    color: var(--color-text);
    font: inherit;
    text-align: left;
    padding: 0.55rem 0.6rem;
    border-radius: 6px;
    cursor: pointer;
  }

  button.item:hover {
    background-color: var(--color-bg-hover);
  }

  .item.danger {
    color: var(--color-danger);
  }

  .theme-toggle-container {
    margin: -0.6rem
  }

  .theme-label {
    color: var(--color-text);
  }
</style>
