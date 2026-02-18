<script lang="ts">
  import { authStore } from "$lib/stores/auth";
  import { goto } from "$app/navigation";
  import { Menu, X, House, User, LogOut } from "@lucide/svelte";

  let show = $state(false);

  function toggle() {
    show = !show;
  }

  function logout() {
    authStore.clearToken();
    goto("/login");
  }
</script>

<div class="sidebar" class:show>
  <button onclick={toggle} class="open-btn">
    <Menu />
  </button>
  <nav class="nav-links">
    <button onclick={() => { toggle(); goto("/"); }} class="nav-link">
      <House />
      Dashboard
    </button>
    <button onclick={() => { toggle(); goto(`/profile/${$authStore.user?.username}`); }} class="nav-link">
      <User />
      Profile
    </button>
    <button onclick={() => { toggle(); logout(); }} class="nav-link">
      <LogOut />
      Logout
    </button>
  </nav>
  <button onclick={toggle} class="close-btn">
    <X />
  </button>
</div>

<style>
  .sidebar {
    box-sizing: border-box;
    position: fixed;
    top: 0;
    left: 0;
    width: 100vw;
    height: 100vh;
    color: white;
    transform: translateX(-100%);
    transition: transform 0.3s ease;
    z-index: 1000;
    padding: 1rem;
    background-color: #333;
  }

  .nav-link {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    color: white;
    text-decoration: none;
    font-size: 1.2rem;
    transition: color 0.2s ease;
    background-color: transparent;
    border: none;
    cursor: pointer;
    padding: 0;
  }

  .sidebar.show {
    transform: translateX(0);
  }

  .open-btn {
    position: absolute;
    top: 1rem;
    right: 0;
    background-color: #333;
    color: white;
    cursor: pointer;
    padding: 0.5rem;
    border-top: 1px solid #555;
    border-bottom: 1px solid #555;
    border-right: 1px solid #555;
    border-left: none;
    border-top-right-radius: 10px;
    border-bottom-right-radius: 10px;
    transform: translateX(100%);
  }

  .close-btn {
    position: absolute;
    top: 1rem;
    right: 1rem;
    background-color: transparent;
    color: white;
    cursor: pointer;
    padding: 0.5rem;
    border: none;
  }

  .nav-links {
    display: flex;
    flex-direction: column;
    gap: 1rem;
  }
</style>
