<script lang="ts">
  import {
    api,
    type UserFramilyInfo,
    type PictureInfo,
    type UserInfo,
  } from "$lib/api";
  import Framilies from "$lib/components/Framilies.svelte";
  import Framily from "$lib/components/Framily.svelte";
  import Galery from "$lib/components/Galery.svelte";
  import Profile from "$lib/components/Profile.svelte";
  import PictureView from "$lib/components/PictureView.svelte";
  import UploadPopup from "$lib/components/UploadPopup.svelte";
  import LayoutDashboard from "@lucide/svelte/icons/layout-dashboard";
  import LayoutList from "@lucide/svelte/icons/layout-list";
  import ImagePlus from "@lucide/svelte/icons/image-plus";
  import User from "@lucide/svelte/icons/user";
  import Menu from "@lucide/svelte/icons/menu";
  import { onMount } from "svelte";
  import { app } from "$lib/app";
  import ConnectFramilyPopup from "$lib/components/ConnectFramilyPopup.svelte";

  const appState = app.state;

  let user: UserInfo | undefined = $state();
  let framilies: UserFramilyInfo[] = $derived(user?.framilies ?? []);
  let dashboardPictures: PictureInfo[] | undefined = $state();
  let uploadPopupOpen = $state(false);
  let uploadDefaultCodes: string[] = $state([]);
  let connectFramilyPopupOpen = $state(false);

  function openUploadPopup(codes: string[]) {
    uploadDefaultCodes = codes;
    uploadPopupOpen = true;
  }

  onMount(async () => {
    const me = await api.auth.me();
    const response = await api.user.getInfo(me.username);
    user = response.user;

    const picturesResponse = await api.pictures.listAll();
    dashboardPictures = picturesResponse.pictures;
  });
</script>

{#if dashboardPictures === undefined || framilies === undefined || user === undefined}
  <div class="page">Loading...</div>
{:else}
  <div class="page">
    <UploadPopup
      {framilies}
      bind:isOpen={uploadPopupOpen}
      framilyCodes={uploadDefaultCodes}
    />
    <ConnectFramilyPopup bind:isOpen={connectFramilyPopupOpen} />
    <div class="topBar">
      <div class="title">Framily</div>
      <button class="button">
        <Menu />
      </button>
    </div>
    <div class="content">
      {#if $appState.page.page === "dashboard"}
        <button
          class="add-picture"
          onclick={() => openUploadPopup(framilies.map((f) => f.code))}
        >
          <ImagePlus size={16} />
          Add picture
        </button>
        <Galery pictures={dashboardPictures} />
      {:else if $appState.page.page === "framilies"}
        <Framilies
          {framilies}
          onAddFramily={() => (connectFramilyPopupOpen = true)}
        />
      {:else if $appState.page.page === "profile"}
        <Profile
          username={$appState.page.username}
          currentUsername={user.username}
          onAddPicture={() => openUploadPopup(framilies.map((f) => f.code))}
        />
      {:else if $appState.page.page === "framily"}
        <Framily
          code={$appState.page.code}
          currentUsername={user.username}
          onAddPicture={(code) => openUploadPopup([code])}
        />
      {:else if $appState.page.page === "picture"}
        <PictureView
          picture={$appState.page.picture}
          currentUsername={user.username}
          myFramilies={framilies}
          onClose={() => app.navigate({ page: "dashboard" })}
        />
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
      <button
        class="button"
        onclick={() =>
          app.navigate({
            page: "profile",
            username: user!.username,
            section: "pictures",
          })}
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
    margin: 1rem 1rem 0;
  }
</style>
