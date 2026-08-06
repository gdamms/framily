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
  import PictureView from "$lib/pages/picture/PictureView.svelte";
  import LoginForm from "$lib/pages/login/LoginForm.svelte";
  import RegisterForm from "$lib/pages/register/RegisterForm.svelte";
  import IconButton from "$lib/ui/IconButton.svelte";
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

  async function refreshUser() {
    if (!user) return;
    const response = await api.user.getInfo(user.username);
    user = response.user;
  }

  async function loadApp() {
    const me = await api.auth.me();
    const response = await api.user.getInfo(me.username);
    user = response.user;

    const picturesResponse = await api.pictures.listAll();
    dashboardPictures = picturesResponse.pictures;
  }

  $effect(() => {
    if ($auth.isAuthenticated) {
      if (!hasLoaded) {
        hasLoaded = true;
        // A stale/invalid cookie fails here with a 401; the api client already
        // clears the auth store in that case, which flips us back to the
        // login screen - just swallow the rejection so it doesn't surface.
        loadApp().catch(() => {});
      }
    } else {
      hasLoaded = false;
      user = undefined;
      dashboardPictures = undefined;
    }
  });
</script>

{#if !$auth.isAuthenticated}
  {#if $authView === "register"}
    <RegisterForm />
  {:else}
    <LoginForm />
  {/if}
{:else if dashboardPictures === undefined || user === undefined}
  <div class="page loading">Loading...</div>
{:else}
  <div class="page">
    <div class="content">
      {#if $appState.page.page === "dashboard"}
        <Dashboard {framilies} pictures={dashboardPictures} section={$appState.page.section} />
      {:else if $appState.page.page === "profile"}
        <Profile username={$appState.page.username} currentUsername={user.username} />
      {:else if $appState.page.page === "framily"}
        <Framily
          code={$appState.page.code}
          currentUsername={user.username}
          {framilies}
          onFramilyDeleted={refreshUser}
        />
      {:else if $appState.page.page === "picture"}
        <PictureView
          picture={$appState.page.picture}
          currentUsername={user.username}
          myFramilies={framilies}
          onClose={() => app.navigate({ page: "dashboard", section: "galery" })}
        />
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
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
    background: #eee;
    display: flex;
    flex-direction: column;
  }

  .page.loading {
    align-items: center;
    justify-content: center;
    color: #888;
  }

  .bottomBar {
    width: 100%;
    box-sizing: border-box;
    display: flex;
    justify-content: space-around;
    align-items: center;
    padding: 0.5rem;
    border-top: 1px solid #ccc;
    background: #eee;
  }

  .content {
    flex: 1;
    min-height: 0;
    overflow: hidden;
    display: flex;
    flex-direction: column;
  }
</style>
