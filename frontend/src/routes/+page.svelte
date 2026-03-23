<script lang="ts">
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { authStore } from "$lib/stores/auth";
  import { api, type FramilyListItem, type PictureInfo } from "$lib/api/index";
  import Button from "$lib/components/Button.svelte";
  import Galery from "$lib/components/Galery.svelte";
  import BottomBar from "$lib/components/BottomBar.svelte";
  import TopBar from "$lib/components/TopBar.svelte";

  let framilies: FramilyListItem[] = [];
  let pendingInvitations: FramilyListItem[] = [];
  let allPictures: PictureInfo[] = [];
  let loading = true;
  let error = "";

  // Connect form state
  let showConnectForm = false;
  let connectCode = "";
  let formError = "";
  let formLoading = false;

  onMount(async () => {
    if (!$authStore.isAuthenticated) {
      await goto("/login");
      return;
    }
    await loadData();
  });

  async function loadData() {
    loading = true;
    error = "";
    try {
      const token = authStore.getToken();
      if (!token) return;

      const [framilyResponse, picturesResponse] = await Promise.all([
        api.framily.list(token),
        api.pictures.listAll(token),
      ]);

      framilies = framilyResponse.framilies.filter((f) => f.role >= 1);
      pendingInvitations = framilyResponse.framilies.filter((f) => f.role === 0);
      allPictures = picturesResponse.pictures;
    } catch (e: any) {
      error = e.message || "Failed to load data";
    } finally {
      loading = false;
    }
  }

  async function connectToFramily() {
    formLoading = true;
    formError = "";
    try {
      const token = authStore.getToken();
      if (!token) return;

      await api.framily.connect(connectCode, token);
      showConnectForm = false;
      connectCode = "";
      await loadData();
    } catch (e: any) {
      formError = e.message || "Failed to connect";
    } finally {
      formLoading = false;
    }
  }

  async function handleInvitation(code: string, accepted: boolean) {
    try {
      const token = authStore.getToken();
      if (!token) return;

      await api.framily.join(code, accepted, token);
      await loadData();
    } catch (e: any) {
      error = e.message || "Failed to respond to invitation";
    }
  }

  function getRoleName(role: number): string {
    switch (role) {
      case 0:
        return "Invited";
      case 1:
        return "Member";
      case 2:
        return "Admin";
      default:
        return "Unknown";
    }
  }
</script>

<div class="dashboard">
  <TopBar />
  <Galery pictures={allPictures} framilies={framilies} />
</div>

<div class="dashboard2">
  <h1>Welcome, {$authStore.user?.display_name}!</h1>

  <BottomBar />

  {#if loading}
    <p class="loading">Loading...</p>
  {:else if error}
    <p class="error">{error}</p>
  {:else}
    <!-- Pending Invitations -->
    {#if pendingInvitations.length > 0}
      <section class="invitations">
        <h2>Pending Invitations</h2>
        <div class="framily-grid">
          {#each pendingInvitations as invite}
            <div class="framily-card invitation">
              <h3>{invite.name}</h3>
              <p class="code">Code: {invite.code}</p>
              <p class="members">
                {invite.member_count} member{invite.member_count !== 1
                  ? "s"
                  : ""}
              </p>
              <div class="invitation-actions">
                <button
                  class="accept-btn"
                  onclick={() => handleInvitation(invite.code, true)}
                  >Accept</button
                >
                <button
                  class="decline-btn"
                  onclick={() => handleInvitation(invite.code, false)}
                  >Decline</button
                >
              </div>
            </div>
          {/each}
        </div>
      </section>
    {/if}

    <!-- My Framilies -->
    <section class="my-framilies">
      <div class="section-header">
        <h2>My Framilies</h2>
        <div class="actions">
          <Button
            onclick={() => {
              showConnectForm = true;
            }}>Connect to Framily</Button
          >
        </div>
      </div>

      <!-- Connect Form Modal -->
      {#if showConnectForm}
        <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
        <div class="modal-overlay" onclick={() => (showConnectForm = false)}>
          <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
          <div class="modal" onclick={(e) => e.stopPropagation()}>
            <h3>Connect to Framily</h3>
            <form
              onsubmit={(e) => {
                e.preventDefault();
                connectToFramily();
              }}
            >
              <input
                type="text"
                placeholder="Framily Code (8 characters)"
                bind:value={connectCode}
                maxlength="8"
              />
              {#if formError}
                <p class="error">{formError}</p>
              {/if}
              <div class="modal-actions">
                <button type="button" onclick={() => (showConnectForm = false)}
                  >Cancel</button
                >
                <button
                  type="submit"
                  disabled={formLoading || connectCode.length !== 8}
                >
                  {formLoading ? "Connecting..." : "Connect"}
                </button>
              </div>
            </form>
          </div>
        </div>
      {/if}

      {#if framilies.length === 0}
        <p class="no-framilies">
          You haven't joined any framilies yet. Connect using a code or ask a
          member to invite you!
        </p>
      {:else}
        <div class="framily-grid">
          {#each framilies as framily}
            <a href="/framily/{framily.code}" class="framily-card">
              <h3>{framily.name}</h3>
              <p class="code">Code: {framily.code}</p>
              <p class="members">
                {framily.member_count} member{framily.member_count !== 1
                  ? "s"
                  : ""}
              </p>
              <p class="role">{getRoleName(framily.role)}</p>
            </a>
          {/each}
        </div>
      {/if}
    </section>

    <!-- All Photos Section -->
    <section class="all-photos">
      <h2>Recent Photos from All Framilies</h2>
      {#if allPictures.length === 0}
        <p class="no-photos">No photos yet. Upload some in your framilies!</p>
      {:else}
        <Galery pictures={allPictures.slice(0, 12)} framilies={framilies} />
        {#if allPictures.length > 12}
          <p class="more-photos">And {allPictures.length - 12} more photos in your framilies...</p>
        {/if}
      {/if}
    </section>
  {/if}
</div>

<style>
  .dashboard2 {
    display: none;
  }

  .dashboard {
    position: relative;
    max-width: 800px;
    height: 100%;
    margin: 0 auto;
    display: flex;
    flex-direction: column;
  }
</style>
