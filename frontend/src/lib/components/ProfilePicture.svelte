<script lang="ts">
  import { api, type UserInfo, type FramilyMember } from "$lib/api";

  export let user: UserInfo | FramilyMember;

  function profilePictureLoaded(event: Event) {
    const img = event.target as HTMLImageElement;
    const placeholder = img.nextElementSibling as HTMLDivElement;
    placeholder.style.display = "none";
    img.style.display = "block";
  }
</script>

<div class="profile-picture">
  <img
    src={api.user.getProfilePictureUrl(user)}
    alt="{user.display_name}'s avatar"
    class="avatar-img"
    onload={profilePictureLoaded}
  />
  <div class="avatar-placeholder">
    {(user.display_name)
      .charAt(0)
      .toUpperCase()}
  </div>
</div>

<style>
  .profile-picture {
    width: 100%;
    height: 100%;
  }

  .avatar-img {
    width: 100%;
    height: 100%;
    border-radius: 50%;
    object-fit: cover;
    display: none;
  }

  .avatar-placeholder {
    width: 100%;
    height: 100%;
    border-radius: 50%;
    background-color: #007bff;
    color: white;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.25rem;
    font-weight: 600;
  }
</style>