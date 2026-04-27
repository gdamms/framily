<script lang="ts">
  import { api, type PictureInfo, type FramilyInfo, type UserInfo } from "$lib/api";
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
  } from "@lucide/svelte";
  import { onMount } from "svelte";

  let pictures: PictureInfo[] = $state([]);
  let framilies: FramilyInfo[] = $state([]);
  let uploadPopupOpen = $state(false);

  type Page = "dashboard" | "framilies" | "profile" | "framily";
  let page: Page = $state("dashboard");
  let selectedFramily: FramilyInfo | null = $state(null);
  let user: UserInfo | null = $state(null);

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
</script>

<div class="page">
  {#if uploadPopupOpen}
    <UploadPopup
      {framilies}
      onClose={closeUploadPopup}
      framilyCodes={framilies.map((f) => f.code)}
    />
  {/if}
  <div class="topBar">
    <div class="title">Framily</div>
    <button class="button">
      <Menu />
    </button>
  </div>
  <div class="content">
    {#if page === "dashboard"}
      <Galery {pictures} />
    {:else if page === "framilies"}
      <Framilies {framilies} />
    {:else if page === "profile" && user}
      <Profile {user} />
    {:else if page === "framily" && selectedFramily}
      <Framily framily={selectedFramily} />
    {/if}
  </div>
  <div class="bottomBar">
    <button class="button" onclick={() => (page = "dashboard")}>
      <LayoutDashboard />
    </button>
    <button class="button" onclick={() => (page = "framilies")}>
      <LayoutList />
    </button>
    <button class="button" onclick={() => (uploadPopupOpen = true)}>
      <ImagePlus />
    </button>
    <button class="button" onclick={() => (page = "profile")}>
      <User />
    </button>
  </div>
</div>

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
