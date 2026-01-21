<script lang="ts">
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { authStore } from "$lib/stores/auth";
  import { api, type FramilyListItem } from "$lib/api";

  let framilies: FramilyListItem[] = [];
  let pendingInvitations: FramilyListItem[] = [];
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
    await loadFramilies();
  });

  async function loadFramilies() {
    loading = true;
    error = "";
    try {
      const token = authStore.getToken();
      if (!token) return;

      const response = await api.framily.list(token);
      framilies = response.framilies.filter((f) => f.role >= 1);
      pendingInvitations = response.framilies.filter((f) => f.role === 0);
    } catch (e: any) {
      error = e.message || "Failed to load framilies";
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
      await loadFramilies();
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
      await loadFramilies();
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
  <h1>Welcome, {$authStore.user?.display_name}!</h1>

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
          <button
            onclick={() => {
              showConnectForm = true;
            }}>Connect to Framily</button
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
  {/if}
</div>

<style>
  .dashboard {
    max-width: 900px;
    margin: 0 auto;
  }

  h1 {
    margin-bottom: 2rem;
  }

  .loading,
  .error {
    padding: 1rem;
    text-align: center;
  }

  .error {
    color: #dc3545;
    background-color: #f8d7da;
    border-radius: 4px;
  }

  section {
    margin-bottom: 2rem;
  }

  .section-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .actions {
    display: flex;
    gap: 0.5rem;
  }

  .actions button {
    padding: 0.5rem 1rem;
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }

  .actions button:hover {
    background-color: #0056b3;
  }

  .framily-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
    gap: 1rem;
  }

  .framily-card {
    background: white;
    padding: 1.5rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    text-decoration: none;
    color: inherit;
    transition:
      transform 0.2s,
      box-shadow 0.2s;
  }

  .framily-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15);
  }

  .framily-card h3 {
    margin: 0 0 0.5rem 0;
    color: #333;
  }

  .framily-card .code {
    font-family: monospace;
    color: #666;
    font-size: 0.9rem;
  }

  .framily-card .members {
    color: #888;
    font-size: 0.9rem;
  }

  .framily-card .role {
    display: inline-block;
    margin-top: 0.5rem;
    padding: 0.25rem 0.5rem;
    background-color: #e9ecef;
    border-radius: 4px;
    font-size: 0.8rem;
  }

  .invitation {
    border: 2px solid #ffc107;
  }

  .invitation-actions {
    display: flex;
    gap: 0.5rem;
    margin-top: 1rem;
  }

  .accept-btn,
  .decline-btn {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }

  .accept-btn {
    background-color: #28a745;
    color: white;
  }

  .decline-btn {
    background-color: #dc3545;
    color: white;
  }

  .no-framilies {
    text-align: center;
    color: #666;
    padding: 2rem;
    background: white;
    border-radius: 8px;
  }

  .modal-overlay {
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: rgba(0, 0, 0, 0.5);
    display: flex;
    justify-content: center;
    align-items: center;
    z-index: 1000;
  }

  .modal {
    background: white;
    padding: 2rem;
    border-radius: 8px;
    min-width: 300px;
    max-width: 400px;
  }

  .modal h3 {
    margin: 0 0 1rem 0;
  }

  .modal input {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    margin-bottom: 1rem;
    box-sizing: border-box;
  }

  .modal-actions {
    display: flex;
    justify-content: flex-end;
    gap: 0.5rem;
  }

  .modal-actions button {
    padding: 0.5rem 1rem;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }

  .modal-actions button[type="button"] {
    background-color: #6c757d;
    color: white;
  }

  .modal-actions button[type="submit"] {
    background-color: #007bff;
    color: white;
  }

  .modal-actions button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }
</style>
