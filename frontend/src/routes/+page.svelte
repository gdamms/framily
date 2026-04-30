<script lang="ts">
  import {
    api,
    type PictureInfo,
    type FramilyInfo,
    type UserInfo,
  } from "$lib/api";
  import Framilies from "$lib/components/Framilies.svelte";
  import Framily from "$lib/components/Framily.svelte";
  import Galery from "$lib/components/Galery.svelte";
  import Profile from "$lib/components/Profile.svelte";
  import UploadPopup from "$lib/components/UploadPopup.svelte";
  import {
    LayoutDashboard,
    LayoutList,
    ImagePlus,
    User,
    Menu,
    ListPlus,
    UserPlus,
  } from "@lucide/svelte";
  import { onMount } from "svelte";
  import { app } from "$lib/app";
  import ConnectFramilyPopup from "$lib/components/ConnectFramilyPopup.svelte";
  import InvitePopup from "$lib/components/InvitePopup.svelte";

  const appState = app.state;

  let pictures: PictureInfo[] | undefined = $state();
  let framilies: FramilyInfo[] | undefined = $state();
  let user: UserInfo | undefined = $state();
  let uploadPopupOpen = $state(false);
  let connectFramilyPopupOpen = $state(false);
  let invitePopupOpen = $state(false);

  onMount(async () => {
    let picResponse = await api.pictures.listAll();
    pictures = picResponse.pictures;

    let famResponse = await api.framily.list();
    framilies = famResponse.framilies;

    user = await api.auth.me();
  });

  function closeUploadPopup() {
    uploadPopupOpen = false;
  }

  function closeConnectFramilyPopup() {
    connectFramilyPopupOpen = false;
  }

  function closeInvitePopup() {
    invitePopupOpen = false;
  }
</script>

{#if pictures === undefined || framilies === undefined || user === undefined}
  <div class="page">Loading...</div>
{:else}
  <div class="page">
    {#if uploadPopupOpen}
      <UploadPopup
        {framilies}
        onClose={closeUploadPopup}
        framilyCodes={framilies.map((f) => f.code)}
      />
    {/if}
    {#if connectFramilyPopupOpen}
      <ConnectFramilyPopup onClose={closeConnectFramilyPopup} />
    {/if}
    {#if invitePopupOpen && $appState.page.page === "framily"}
      <InvitePopup framilyCode={$appState.page.code} onClose={closeInvitePopup} />
    {/if}
    <div class="topBar">
      <div class="title">Framily</div>
      <button class="button">
        <Menu />
      </button>
    </div>
    <div class="content">
      {#if $appState.page.page === "dashboard"}
        <Galery {pictures} />
      {:else if $appState.page.page === "framilies"}
        <Framilies {framilies} />
      {:else if $appState.page.page === "profile"}
        <Profile username={$appState.page.username} />
      {:else if $appState.page.page === "framily"}
        <Framily code={$appState.page.code} />
      {:else if $appState.page.page === "picture"}
        Not implemented yet
      {/if}
    </div>
    <div class="bottomBar">
      <button
        class="button"
        onclick={() => app.navigate({ page: "dashboard" })}
      >
        <LayoutDashboard />
      </button>
      <button
        class="button"
        onclick={() => app.navigate({ page: "framilies" })}
      >
        <LayoutList />
      </button>
      {#if $appState.page.page === "dashboard"}
        <button class="button" onclick={() => (uploadPopupOpen = true)}>
          <ImagePlus />
        </button>
      {:else if $appState.page.page === "framilies"}
        <button class="button" onclick={() => (connectFramilyPopupOpen = true)}>
          <ListPlus />
        </button>
      {:else if $appState.page.page === "framily" && $appState.page.section === "pictures"}
        <button class="button" onclick={() => (uploadPopupOpen = true)}>
          <ImagePlus />
        </button>
      {:else if $appState.page.page === "framily" && $appState.page.section === "members"}
        <button class="button" onclick={() => (invitePopupOpen = true)}>
          <UserPlus />
        </button>
      {/if}
      <button
        class="button"
        onclick={() =>
          app.navigate({ page: "profile", username: user.username, section: "pictures" })}
      >
        <User />
      </button>
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

  .button {
    background: none;
    border: none;
    padding: 0.5rem;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
  }

  .topBar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0.5rem;
    width: 100%;
    box-sizing: border-box;
    background: #eee;
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

  .hidden {
    display: none;
  }

  .content {
    flex: 1;
    overflow-y: auto;
  }
</style>
