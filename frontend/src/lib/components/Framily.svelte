<script lang="ts">
  import { onMount } from "svelte";
  import { api, type FramilyInfo, type PictureInfo } from "$lib/api";
  import Galery from "./Galery.svelte";
  import Members from "./Members.svelte";
  import { app } from "$lib/app";

  interface Props {
    code: string;
  }

  let { code }: Props = $props();

  let appState = app.state;

  let framily: FramilyInfo | undefined = $state();
  let pictures: PictureInfo[] = $state([]);

  onMount(async () => {
    let infoResponse = await api.framily.info(code);
    framily = infoResponse.framily;

    let picResponse = await api.pictures.list({
      framily_code: framily.code,
    });
    pictures = picResponse.pictures;
  });
</script>

{#if framily === undefined}
  <div class="framily-page">Loading...</div>
{:else if $appState.page.page !== "framily"}
  <div class="framily-page">Framily not found</div>
{:else}
  <div class="framily-page">
    <div class="framily-header">
      <div class="framily-name">{framily.name}</div>
      <div class="framily-code">@{framily.code}</div>
    </div>
    <div class="framily-nav">
      <button
        class="button"
        class:selected={$appState.page.section === "pictures"}
        onclick={() => (app.navigate({ page: "framily", code: framily.code, section: "pictures" }))}
      >
        Pictures
      </button>
      <button
        class="button"
        class:selected={$appState.page.section === "members"}
        onclick={() => (app.navigate({ page: "framily", code: framily.code, section: "members" }))}
      >
        Members
      </button>
      <button
        class="button"
        class:selected={$appState.page.section === "settings"}
        onclick={() => (app.navigate({ page: "framily", code: framily.code, section: "settings" }))}
      >
        Settings
      </button>
    </div>
    <div class="framily-content">
      {#if $appState.page.section === "pictures"}
        <Galery {pictures} />
      {:else if $appState.page.section === "members"}
        <Members members={framily.members} />
      {:else if $appState.page.section === "settings"}
        <div class="settings">
          <h3>Settings</h3>
          <p>This is where you can manage your framily settings.</p>
        </div>
      {/if}
    </div>
  </div>
{/if}

<style>
  .framily-page {
    flex: 1;
    display: flex;
    flex-direction: column;
    height: 100%;
  }

  .framily-header {
    background: #eee;
    padding: 0 1rem;
  }

  .framily-name {
    font-size: 24px;
    font-weight: bold;
  }

  .framily-code {
    font-size: 14px;
    color: #666;
  }

  .framily-nav {
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
    font-weight: bold;
    border-bottom: 2px solid #333;
  }

  .framily-content {
    flex: 1;
  }
</style>
