<script lang="ts">
  import {
    api,
    type UserFramilyInfo,
    type PictureInfo,
    type UserInfo,
  } from "$lib/api";
  import Dashboard from "$lib/pages/dashboard/Dashboard.svelte";
  import Framily from "$lib/pages/framily/Framily.svelte";
  import Profile from "$lib/pages/profile/Profile.svelte";
  import Settings from "$lib/pages/settings/Settings.svelte";
  import LoginForm from "$lib/pages/login/LoginForm.svelte";
  import RegisterForm from "$lib/pages/register/RegisterForm.svelte";
  import LoadingPage from "$lib/ui/LoadingPage.svelte";
  import ErrorPage from "$lib/ui/ErrorPage.svelte";
  import IconButton from "$lib/ui/IconButton.svelte";
  import BurgerMenu from "$lib/ui/BurgerMenu.svelte";
  import LayoutDashboard from "@lucide/svelte/icons/layout-dashboard";
  import User from "@lucide/svelte/icons/user";
  import { app, authView } from "$lib/app";
  import { authStore } from "$lib/stores/auth";

  const appState = app.state;
  const auth = authStore;

  let user: UserInfo | undefined = $state();
  let framilies: UserFramilyInfo[] = $derived(user?.framilies ?? []);
  let dashboardPictures: PictureInfo[] | undefined = $state();
  let hasLoaded = $state(false);
  let loadError: string | undefined = $state();

  async function refreshUser() {
    if (!user) return;
    const response = await api.user.getInfo(user.username);
    user = response.user;
  }

  async function refreshPictures() {
    const picturesResponse = await api.pictures.listAll();
    dashboardPictures = picturesResponse.pictures;
  }

  async function loadApp() {
    loadError = undefined;
    try {
      const me = await api.auth.me();
      const response = await api.user.getInfo(me.username);
      user = response.user;

      const picturesResponse = await api.pictures.listAll();
      dashboardPictures = picturesResponse.pictures;
    } catch (error: any) {
      // A stale/invalid token 401s here; the api client already clears the
      // auth store in that case, which flips us back to the login screen -
      // only surface an error for failures that don't already self-resolve
      // (network errors, 5xx, ...), instead of leaving the loading spinner
      // spinning forever.
      if (error?.status !== 401) {
        loadError = error?.message || "Failed to load your data";
      }
    }
  }

  $effect(() => {
    if ($auth.isAuthenticated) {
      if (!hasLoaded) {
        hasLoaded = true;
        loadApp();
      }
    } else {
      hasLoaded = false;
      user = undefined;
      dashboardPictures = undefined;
      loadError = undefined;
    }
  });
</script>

{#if !$auth.isAuthenticated}
  {#if $authView === "register"}
    <RegisterForm />
  {:else}
    <LoginForm />
  {/if}
{:else if loadError}
  <div class="page">
    <ErrorPage
      message={loadError}
      onRetry={loadApp}
      onBack={() => authStore.clearToken()}
      backLabel="Log out"
    />
  </div>
{:else if dashboardPictures === undefined || user === undefined}
  <div class="page">
    <LoadingPage />
  </div>
{:else}
  <div class="page">
    <div class="burger-container">
      <BurgerMenu currentUsername={user.username} />
    </div>
    <div class="content">
      {#if $appState.page.page === "dashboard"}
        <Dashboard
          {framilies}
          pictures={dashboardPictures}
          section={$appState.page.section}
          currentUsername={user.username}
          onPicturesChanged={refreshPictures}
          onFramiliesChanged={refreshUser}
        />
      {:else if $appState.page.page === "profile"}
        <Profile
          username={$appState.page.username}
          currentUsername={user.username}
          myFramilies={framilies}
        />
      {:else if $appState.page.page === "framily"}
        <Framily
          code={$appState.page.code}
          currentUsername={user.username}
          {framilies}
          onFramilyDeleted={refreshUser}
        />
      {:else if $appState.page.page === "settings"}
        <Settings user={user!} onChanged={refreshUser} />
      {/if}
    </div>
    <div class="bottomBar">
      <IconButton
        icon={LayoutDashboard}
        onclick={() => app.navigate({ page: "dashboard", section: "galery" })}
      />
      <IconButton
        icon={User}
        onclick={() =>
          app.navigate({
            page: "profile",
            username: user!.username,
            section: "pictures",
          })}
      />
    </div>
  </div>
{/if}

<style>
  .page {
    position: relative;
    max-width: 800px;
    margin: 0 auto;
    height: 100%;
    box-shadow: 0 0 10px var(--color-shadow);
    background: var(--color-bg-page);
    color: var(--color-text);
    display: flex;
    flex-direction: column;
  }

  .burger-container {
    position: absolute;
    top: 0.5rem;
    right: 0.5rem;
    z-index: 100;
  }

  .bottomBar {
    width: 100%;
    box-sizing: border-box;
    display: flex;
    justify-content: space-around;
    align-items: center;
    padding: 0.5rem;
    border-top: 1px solid var(--color-border);
    background: var(--color-bg-page);
  }

  .content {
    flex: 1;
    min-height: 0;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }
</style>
