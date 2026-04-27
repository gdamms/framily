<script lang="ts">
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { page } from "$app/stores";
  import { authStore } from "$lib/stores/auth";
  import { api, type FramilyInfo, type PictureInfo } from "$lib/api/index";
  import ProfilePicture from "$lib/components/ProfilePicture.svelte";

  let framily: FramilyInfo | null = null;
  let pictures: PictureInfo[] = [];
  let loading = true;
  let error = "";
  let activeTab: "gallery" | "members" | "settings" = "gallery";

  // Upload state
  let uploading = false;
  let uploadError = "";
  let fileInput: HTMLInputElement;

  // Invite state
  let showInviteModal = false;
  let inviteUsername = "";
  let inviteError = "";
  let inviteLoading = false;

  // Settings state
  let settingsForm = {
    picture_duration: 10,
    shuffle_mode: "random",
    transition_effect: "fade",
  };
  let settingsLoading = false;
  let settingsError = "";
  let settingsSuccess = "";

  $: framilyCode = $page.params.code || "";
  $: userRole =
    framily?.members?.find((m) => m.username === $authStore.user?.username)
      ?.role ?? -1;
  $: isAdmin = userRole === 2;

  onMount(async () => {
    if (!$authStore.isAuthenticated) {
      await goto("/login");
      return;
    }
    await loadFramilyData();
  });

  async function loadFramilyData() {
    loading = true;
    error = "";
    try {
      const [framilyResponse, picturesResponse] = await Promise.all([
        api.framily.info(framilyCode),
        api.pictures.list({ framily_code: framilyCode }),
      ]);

      framily = framilyResponse.framily;
      pictures = picturesResponse.pictures;

      // Initialize settings form
      if (framily.settings) {
        settingsForm = {
          picture_duration: framily.settings.picture_duration,
          shuffle_mode: framily.settings.shuffle_mode,
          transition_effect: framily.settings.transition_effect,
        };
      }
    } catch (e: any) {
      error = e.message || "Failed to load framily";
    } finally {
      loading = false;
    }
  }

  async function handleUpload(event: Event) {
    const target = event.target as HTMLInputElement;
    const file = target.files?.[0];
    if (!file) return;

    uploading = true;
    uploadError = "";
    try {
      await api.pictures.upload([framilyCode], file);
      await loadFramilyData();
    } catch (e: any) {
      uploadError = e.message || "Failed to upload";
    } finally {
      uploading = false;
      if (fileInput) fileInput.value = "";
    }
  }

  async function inviteUser() {
    inviteLoading = true;
    inviteError = "";
    try {
      await api.framily.invite(framilyCode, inviteUsername);
      showInviteModal = false;
      inviteUsername = "";
      await loadFramilyData();
    } catch (e: any) {
      inviteError = e.message || "Failed to invite";
    } finally {
      inviteLoading = false;
    }
  }

  async function kickMember(username: string) {
    if (!confirm(`Are you sure you want to kick ${username}?`)) return;

    try {
      await api.framily.kick(framilyCode, username);
      await loadFramilyData();
    } catch (e: any) {
      alert(e.message || "Failed to kick member");
    }
  }

  async function promoteMember(username: string, newRole: number) {
    try {
      await api.framily.promote(framilyCode, username, newRole);
      await loadFramilyData();
    } catch (e: any) {
      alert(e.message || "Failed to change role");
    }
  }

  async function saveSettings() {
    settingsLoading = true;
    settingsError = "";
    settingsSuccess = "";
    try {
      await api.framily.updateSettings(framilyCode, settingsForm);
      settingsSuccess = "Settings saved!";
      setTimeout(() => (settingsSuccess = ""), 3000);
    } catch (e: any) {
      settingsError = e.message || "Failed to save settings";
    } finally {
      settingsLoading = false;
    }
  }

  async function leaveFramily() {
    if (!confirm("Are you sure you want to leave this framily?")) return;

    try {
      await api.framily.leave(framilyCode);
      await goto("/");
    } catch (e: any) {
      alert(e.message || "Failed to leave framily");
    }
  }

  async function deleteFramily() {
    if (
      !confirm(
        "Are you sure you want to DELETE this framily? This cannot be undone!",
      )
    )
      return;
    if (!confirm("Really delete? All photos and data will be lost!")) return;

    try {
      await api.framily.delete(framilyCode);
      await goto("/");
    } catch (e: any) {
      alert(e.message || "Failed to delete framily");
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

  function canRemovePicture(picture: PictureInfo): boolean {
    return isAdmin || picture.uploader_username === $authStore.user?.username;
  }

  function removePicture(pictureId: string) {
    return api.pictures.removeVisibility(pictureId, [framilyCode]);
  }

  async function fetchImageOnError(event: Event): Promise<void> {
    const img = event.target as HTMLImageElement;
    img.onerror = null; // Prevent infinite loop

    const src = img.src;
    const pictureId = src.split("/").pop()?.split("?")[0];
    if (!pictureId) {
      return;
    }

    try {
      const blob = await api.pictures.getImageBlob(pictureId);
      img.src = URL.createObjectURL(blob);
    } catch {
      // Keep the original failed image source.
    }
  }
</script>

<div class="framily-page">
  {#if loading}
    <p class="loading">Loading...</p>
  {:else if error}
    <p class="error">{error}</p>
    <a href="/">← Back to Dashboard</a>
  {:else if framily}
    <header>
      <div class="header-info">
        <h1>{framily.name}</h1>
        <p class="code">Code: <code>{framily.code}</code></p>
      </div>
      <nav class="tabs">
        <button
          class:active={activeTab === "gallery"}
          onclick={() => (activeTab = "gallery")}
        >
          Gallery ({pictures.length})
        </button>
        <button
          class:active={activeTab === "members"}
          onclick={() => (activeTab = "members")}
        >
          Members ({framily.members?.length || 0})
        </button>
        {#if isAdmin}
          <button
            class:active={activeTab === "settings"}
            onclick={() => (activeTab = "settings")}
          >
            Settings
          </button>
        {/if}
      </nav>
    </header>

    <!-- Gallery Tab -->
    {#if activeTab === "gallery"}
      <section class="gallery-section">
        <div class="gallery-header">
          <h2>Photos</h2>
          <div class="upload-area">
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp,image/gif"
              onchange={handleUpload}
              bind:this={fileInput}
              disabled={uploading}
            />
            {#if uploading}
              <span class="uploading">Uploading...</span>
            {/if}
          </div>
        </div>

        {#if uploadError}
          <p class="error">{uploadError}</p>
        {/if}

        {#if pictures.length === 0}
          <p class="no-pictures">No photos yet. Upload the first one!</p>
        {:else}
          <div class="gallery-grid">
            {#each pictures as picture}
              <div class="picture-card">
                <img
                  src={api.pictures.getImageUrl(picture)}
                  alt="Uploaded by {picture.uploader_display_name}"
                  onerror={fetchImageOnError}
                />
                <div class="picture-info">
                  <span class="uploader"
                    >{picture.uploader_display_name || "Unknown"}</span
                  >
                  <span class="date"
                    >{new Date(picture.upload_date).toLocaleDateString()}</span
                  >
                  {#if picture.framilies && picture.framilies.length > 1}
                    <span class="shared-badge" title="Shared with: {picture.framilies.map(f => f.name).join(', ')}">
                      📁 {picture.framilies.length}
                    </span>
                  {/if}
                  {#if canRemovePicture(picture)}
                    <button
                      class="delete-btn"
                      onclick={() => removePicture(picture.id)}
                    >
                      Remove
                    </button>
                  {/if}
                </div>
              </div>
            {/each}
          </div>
        {/if}
      </section>
    {/if}

    <!-- Members Tab -->
    {#if activeTab === "members"}
      <section class="members-section">
        <div class="members-header">
          <h2>Members</h2>
          {#if isAdmin}
            <button class="invite-btn" onclick={() => (showInviteModal = true)}>
              Invite Member
            </button>
          {/if}
        </div>

        <div class="members-list">
          {#each framily.members || [] as member}
            <div class="member-card">
              <div class="member-avatar">
                <ProfilePicture user={member} />
              </div>
              <div class="member-info">
                <a href="/profile/{member.username}" class="member-name-link">
                  <strong>{member.display_name}</strong>
                </a>
                <span class="username">@{member.username}</span>
                <span class="role-badge role-{member.role}"
                  >{getRoleName(member.role)}</span
                >
              </div>
              <div class="member-meta">
                Joined: {new Date(member.joined_date).toLocaleDateString()}
              </div>
              {#if isAdmin && member.username !== $authStore.user?.username && member.role >= 1}
                <div class="member-actions">
                  {#if member.role === 1}
                    <button onclick={() => promoteMember(member.username, 2)}>
                      Make Admin
                    </button>
                  {:else if member.role === 2}
                    <button onclick={() => promoteMember(member.username, 1)}>
                      Demote to Member
                    </button>
                  {/if}
                  <button
                    class="kick-btn"
                    onclick={() => kickMember(member.username)}
                  >
                    Kick
                  </button>
                </div>
              {/if}
            </div>
          {/each}
        </div>

        <div class="member-actions-section">
          <button class="leave-btn" onclick={leaveFramily}>Leave Framily</button
          >
        </div>
      </section>

      <!-- Invite Modal -->
      {#if showInviteModal}
        <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
        <div class="modal-overlay" onclick={() => (showInviteModal = false)}>
          <!-- svelte-ignore a11y_click_events_have_key_events a11y_no_static_element_interactions -->
          <div class="modal" onclick={(e) => e.stopPropagation()}>
            <h3>Invite Member</h3>
            <form
              onsubmit={(e) => {
                e.preventDefault();
                inviteUser();
              }}
            >
              <input
                type="text"
                placeholder="Username"
                bind:value={inviteUsername}
              />
              {#if inviteError}
                <p class="error">{inviteError}</p>
              {/if}
              <div class="modal-actions">
                <button type="button" onclick={() => (showInviteModal = false)}
                  >Cancel</button
                >
                <button
                  type="submit"
                  disabled={inviteLoading || !inviteUsername}
                >
                  {inviteLoading ? "Inviting..." : "Invite"}
                </button>
              </div>
            </form>
          </div>
        </div>
      {/if}
    {/if}

    <!-- Settings Tab -->
    {#if activeTab === "settings" && isAdmin}
      <section class="settings-section">
        <h2>Frame Settings</h2>

        <form
          onsubmit={(e) => {
            e.preventDefault();
            saveSettings();
          }}
        >
          <div class="form-group">
            <label for="picture_duration">Picture Duration (seconds)</label>
            <input
              type="number"
              id="picture_duration"
              bind:value={settingsForm.picture_duration}
              min="1"
              max="300"
            />
          </div>

          <div class="form-group">
            <label for="shuffle_mode">Shuffle Mode</label>
            <select id="shuffle_mode" bind:value={settingsForm.shuffle_mode}>
              <option value="random">Random</option>
              <option value="sequential">Sequential</option>
            </select>
          </div>

          <div class="form-group">
            <label for="transition_effect">Transition Effect</label>
            <select
              id="transition_effect"
              bind:value={settingsForm.transition_effect}
            >
              <option value="fade">Fade</option>
              <option value="slide">Slide</option>
              <option value="none">None</option>
            </select>
          </div>

          {#if settingsError}
            <p class="error">{settingsError}</p>
          {/if}
          {#if settingsSuccess}
            <p class="success">{settingsSuccess}</p>
          {/if}

          <button type="submit" disabled={settingsLoading}>
            {settingsLoading ? "Saving..." : "Save Settings"}
          </button>
        </form>

        <hr />

        <div class="danger-zone">
          <h3>Danger Zone</h3>
          <button class="delete-framily-btn" onclick={deleteFramily}>
            Delete Framily
          </button>
          <p class="warning">
            This will permanently delete all photos and data.
          </p>
        </div>
      </section>
    {/if}
  {/if}
</div>

<style>
  .framily-page {
    max-width: 1000px;
    margin: 0 auto;
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

  .success {
    color: #155724;
    background-color: #d4edda;
    border-radius: 4px;
    padding: 0.5rem;
  }

  header {
    margin-bottom: 2rem;
  }

  .header-info h1 {
    margin: 0 0 0.5rem 0;
  }

  .code {
    color: #666;
  }

  .code code {
    font-family: monospace;
    background-color: #f0f0f0;
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
  }

  .tabs {
    display: flex;
    gap: 0.5rem;
    margin-top: 1rem;
    border-bottom: 2px solid #e0e0e0;
    padding-bottom: 0;
  }

  .tabs button {
    padding: 0.75rem 1.5rem;
    border: none;
    background: none;
    cursor: pointer;
    border-bottom: 2px solid transparent;
    margin-bottom: -2px;
  }

  .tabs button.active {
    border-bottom-color: #007bff;
    color: #007bff;
  }

  /* Gallery Styles */
  .gallery-header,
  .members-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
  }

  .upload-area input {
    padding: 0.5rem;
  }

  .uploading {
    color: #666;
    margin-left: 1rem;
  }

  .no-pictures {
    text-align: center;
    color: #666;
    padding: 3rem;
    background: white;
    border-radius: 8px;
  }

  .gallery-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
    gap: 1rem;
  }

  .picture-card {
    background: white;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
  }

  .picture-card img {
    width: 100%;
    height: 200px;
    object-fit: cover;
  }

  .picture-info {
    padding: 0.75rem;
    display: flex;
    flex-wrap: wrap;
    gap: 0.5rem;
    align-items: center;
  }

  .picture-info .uploader {
    font-weight: 500;
  }

  .picture-info .date {
    color: #888;
    font-size: 0.85rem;
  }

  .picture-info .delete-btn {
    margin-left: auto;
    padding: 0.25rem 0.5rem;
    background-color: #dc3545;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.8rem;
  }

  /* Members Styles */
  .invite-btn {
    padding: 0.5rem 1rem;
    background-color: #28a745;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }

  .members-list {
    display: flex;
    flex-direction: column;
    gap: 0.75rem;
  }

  .member-card {
    background: white;
    padding: 1rem;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    display: flex;
    flex-wrap: wrap;
    gap: 1rem;
    align-items: flex-start;
  }

  .member-avatar {
    width: 48px;
    height: 48px;
    flex-shrink: 0;
  }

  .member-name-link {
    text-decoration: none;
    color: inherit;
  }

  .member-name-link:hover {
    text-decoration: underline;
    color: #007bff;
  }

  .member-info {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    flex-wrap: wrap;
    flex: 1;
  }

  .member-info .username {
    color: #888;
  }

  .role-badge {
    padding: 0.25rem 0.5rem;
    border-radius: 4px;
    font-size: 0.8rem;
  }

  .role-badge.role-0 {
    background-color: #ffc107;
    color: #333;
  }

  .role-badge.role-1 {
    background-color: #17a2b8;
    color: white;
  }

  .role-badge.role-2 {
    background-color: #28a745;
    color: white;
  }

  .member-meta {
    color: #888;
    font-size: 0.85rem;
    margin-top: 0.5rem;
  }

  .member-actions {
    margin-top: 0.75rem;
    display: flex;
    gap: 0.5rem;
  }

  .member-actions button {
    padding: 0.25rem 0.5rem;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.85rem;
    background-color: #007bff;
    color: white;
  }

  .member-actions .kick-btn {
    background-color: #dc3545;
  }

  .member-actions-section {
    margin-top: 2rem;
    padding-top: 1rem;
    border-top: 1px solid #e0e0e0;
  }

  .leave-btn {
    padding: 0.5rem 1rem;
    background-color: #dc3545;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }

  /* Settings Styles */
  .settings-section form {
    background: white;
    padding: 1.5rem;
    border-radius: 8px;
    max-width: 400px;
  }

  .form-group {
    margin-bottom: 1rem;
  }

  .form-group label {
    display: block;
    margin-bottom: 0.5rem;
    font-weight: 500;
  }

  .form-group input,
  .form-group select {
    width: 100%;
    padding: 0.5rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    box-sizing: border-box;
  }

  .settings-section form button[type="submit"] {
    padding: 0.75rem 1.5rem;
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }

  .settings-section form button:disabled {
    opacity: 0.5;
  }

  .danger-zone {
    margin-top: 2rem;
    padding: 1rem;
    background: #fff5f5;
    border: 1px solid #dc3545;
    border-radius: 8px;
  }

  .danger-zone h3 {
    color: #dc3545;
    margin: 0 0 1rem 0;
  }

  .delete-framily-btn {
    padding: 0.5rem 1rem;
    background-color: #dc3545;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
  }

  .warning {
    color: #666;
    font-size: 0.9rem;
    margin-top: 0.5rem;
  }

  hr {
    margin: 2rem 0;
    border: none;
    border-top: 1px solid #e0e0e0;
  }

  .shared-badge {
    display: inline-block;
    background-color: #e3f2fd;
    color: #1976d2;
    padding: 0.2rem 0.5rem;
    border-radius: 12px;
    font-size: 0.75rem;
    cursor: help;
  }

  /* Modal Styles */
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
</style>
