<script lang="ts">
  import { onMount } from "svelte";
  import { goto } from "$app/navigation";
  import { page } from "$app/stores";
  import { authStore } from "$lib/stores/auth";
  import { api, type UserInfo } from "$lib/api";

  let user: UserInfo | null = null;
  let loading = true;
  let error = "";
  let isOwnProfile = false;

  // Edit state
  let editing = false;
  let editForm = {
    display_name: "",
    email: "",
  };
  let editLoading = false;
  let editError = "";
  let editSuccess = "";

  // Profile picture state
  let uploadingPicture = false;
  let pictureError = "";
  let fileInput: HTMLInputElement;

  $: username = $page.params.username;

  onMount(async () => {
    if (!$authStore.isAuthenticated) {
      await goto("/login");
      return;
    }
    await loadUserProfile();
  });

  async function loadUserProfile() {
    loading = true;
    error = "";
    try {
      const token = authStore.getToken();
      if (!token) return;

      const response = await api.user.getInfo(username, token);
      user = response.user;
      isOwnProfile = user.id === $authStore.user?.id;

      // Initialize edit form
      editForm = {
        display_name: user.display_name || "",
        email: user.email || "",
      };
    } catch (e: any) {
      error = e.message || "Failed to load profile";
    } finally {
      loading = false;
    }
  }

  async function saveProfile() {
    editLoading = true;
    editError = "";
    editSuccess = "";
    try {
      const token = authStore.getToken();
      if (!token) return;

      const response = await api.user.updateProfile(
        {
          display_name: editForm.display_name,
          email: editForm.email,
        },
        token
      );
      user = response.user;
      editing = false;
      editSuccess = "Profile updated successfully!";
      setTimeout(() => (editSuccess = ""), 3000);

      // Update auth store if this is our profile
      if (isOwnProfile) {
        authStore.updateUser(response.user);
      }
    } catch (e: any) {
      editError = e.message || "Failed to update profile";
    } finally {
      editLoading = false;
    }
  }

  async function handlePictureUpload(event: Event) {
    const target = event.target as HTMLInputElement;
    const file = target.files?.[0];
    if (!file) return;

    uploadingPicture = true;
    pictureError = "";
    try {
      const token = authStore.getToken();
      if (!token) return;

      await api.user.uploadProfilePicture(file, token);
      await loadUserProfile();

      // Refresh auth store user data
      if (isOwnProfile) {
        const meResponse = await api.auth.me(token);
        authStore.updateUser(meResponse);
      }
    } catch (e: any) {
      pictureError = e.message || "Failed to upload picture";
    } finally {
      uploadingPicture = false;
      if (fileInput) fileInput.value = "";
    }
  }

  async function deletePicture() {
    if (!confirm("Are you sure you want to delete your profile picture?"))
      return;

    try {
      const token = authStore.getToken();
      if (!token) return;

      await api.user.deleteProfilePicture(token);
      await loadUserProfile();

      // Refresh auth store user data
      if (isOwnProfile) {
        const meResponse = await api.auth.me(token);
        authStore.updateUser(meResponse);
      }
    } catch (e: any) {
      pictureError = e.message || "Failed to delete picture";
    }
  }

  function cancelEdit() {
    editing = false;
    editError = "";
    editForm = {
      display_name: user?.display_name || "",
      email: user?.email || "",
    };
  }
</script>

<div class="profile-page">
  {#if loading}
    <p class="loading">Loading...</p>
  {:else if error}
    <p class="error">{error}</p>
    <a href="/">← Back to Dashboard</a>
  {:else if user}
    <div class="profile-header">
      <div class="profile-avatar">
        <img
          src={api.user.getProfilePictureUrl(user)}
          alt="{user.display_name || user.username}'s avatar"
          class="avatar-large"
        />
        <div class="avatar-placeholder-large">
          {(user.display_name || user.username).charAt(0).toUpperCase()}
        </div>

        {#if isOwnProfile}
          <div class="avatar-actions">
            <input
              type="file"
              accept="image/jpeg,image/png,image/webp,image/gif"
              bind:this={fileInput}
              onchange={handlePictureUpload}
              hidden
            />
            <button
              class="btn-secondary"
              onclick={() => fileInput?.click()}
              disabled={uploadingPicture}
            >
              {uploadingPicture ? "Uploading..." : "Change Picture"}
            </button>
            <button class="btn-danger-small" onclick={deletePicture}>
              Remove
            </button>
          </div>
          {#if pictureError}
            <p class="error small">{pictureError}</p>
          {/if}
        {/if}
      </div>

      <div class="profile-info">
        <h1>{user.display_name || user.username}</h1>
        <p class="username">@{user.username}</p>

        {#if editSuccess}
          <p class="success">{editSuccess}</p>
        {/if}

        {#if !editing}
          <div class="profile-details">
            {#if user.email}
              <div class="detail-row">
                <span class="label">Email:</span>
                <span>{user.email}</span>
              </div>
            {/if}
            {#if user.created_at}
              <div class="detail-row">
                <span class="label">Member since:</span>
                <span>{new Date(user.created_at).toLocaleDateString()}</span>
              </div>
            {/if}
          </div>

          {#if isOwnProfile}
            <button class="btn-primary" onclick={() => (editing = true)}>
              Edit Profile
            </button>
          {/if}
        {:else}
          <form
            class="edit-form"
            onsubmit={(e) => {
              e.preventDefault();
              saveProfile();
            }}
          >
            <div class="form-group">
              <label for="display_name">Display Name</label>
              <input
                type="text"
                id="display_name"
                bind:value={editForm.display_name}
                placeholder="Your display name"
              />
            </div>

            <div class="form-group">
              <label for="email">Email</label>
              <input
                type="email"
                id="email"
                bind:value={editForm.email}
                placeholder="your@email.com"
              />
            </div>

            {#if editError}
              <p class="error">{editError}</p>
            {/if}

            <div class="form-actions">
              <button type="button" class="btn-secondary" onclick={cancelEdit}>
                Cancel
              </button>
              <button type="submit" class="btn-primary" disabled={editLoading}>
                {editLoading ? "Saving..." : "Save Changes"}
              </button>
            </div>
          </form>
        {/if}
      </div>
    </div>

    <div class="back-link">
      <a href="/">← Back to Dashboard</a>
    </div>
  {/if}
</div>

<style>
  .profile-page {
    max-width: 800px;
    margin: 0 auto;
    padding: 2rem;
  }

  .loading {
    text-align: center;
    color: #666;
  }

  .error {
    color: #dc3545;
    margin-bottom: 1rem;
  }

  .error.small {
    font-size: 0.85rem;
    margin-top: 0.5rem;
  }

  .success {
    color: #28a745;
    margin-bottom: 1rem;
  }

  .profile-header {
    display: flex;
    gap: 2rem;
    background: white;
    padding: 2rem;
    border-radius: 12px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  }

  .profile-avatar {
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 1rem;
  }

  .avatar-large {
    width: 150px;
    height: 150px;
    border-radius: 50%;
    object-fit: cover;
    border: 4px solid #e0e0e0;
  }

  .avatar-placeholder-large {
    width: 150px;
    height: 150px;
    border-radius: 50%;
    background: linear-gradient(135deg, #007bff 0%, #0056b3 100%);
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 4rem;
    font-weight: 600;
    border: 4px solid #e0e0e0;
  }

  .avatar-actions {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
    justify-content: center;
  }

  .profile-info {
    flex: 1;
  }

  .profile-info h1 {
    margin: 0 0 0.25rem 0;
    font-size: 2rem;
  }

  .username {
    color: #888;
    font-size: 1.1rem;
    margin: 0 0 1.5rem 0;
  }

  .profile-details {
    margin-bottom: 1.5rem;
  }

  .detail-row {
    margin-bottom: 0.5rem;
  }

  .detail-row .label {
    font-weight: 500;
    margin-right: 0.5rem;
    color: #555;
  }

  .edit-form {
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

  .form-group input {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #ccc;
    border-radius: 4px;
    font-size: 1rem;
    box-sizing: border-box;
  }

  .form-actions {
    display: flex;
    gap: 0.5rem;
    margin-top: 1rem;
  }

  .btn-primary {
    padding: 0.75rem 1.5rem;
    background-color: #007bff;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;
  }

  .btn-primary:hover {
    background-color: #0056b3;
  }

  .btn-primary:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .btn-secondary {
    padding: 0.5rem 1rem;
    background-color: #6c757d;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9rem;
  }

  .btn-secondary:hover {
    background-color: #545b62;
  }

  .btn-secondary:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .btn-danger-small {
    padding: 0.5rem 1rem;
    background-color: #dc3545;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 0.9rem;
  }

  .btn-danger-small:hover {
    background-color: #c82333;
  }

  .back-link {
    margin-top: 2rem;
  }

  .back-link a {
    color: #007bff;
    text-decoration: none;
  }

  .back-link a:hover {
    text-decoration: underline;
  }

  @media (max-width: 600px) {
    .profile-header {
      flex-direction: column;
      align-items: center;
      text-align: center;
    }

    .profile-info h1 {
      font-size: 1.5rem;
    }
  }
</style>
