<script lang="ts">
  import { goto } from "$app/navigation";
  import { authStore } from "$lib/stores/auth";
  import NavButton from "$lib/components/NavButton.svelte";

  let isOpen = $state(false);

  function toggle() {
    isOpen = !isOpen;
  }

  function handleLogout() {
    authStore.clearToken();
    goto("/login");
  }
</script>

<nav class="nav">
  <div class="nav-content" class:closed={!isOpen}>
    <button class="nav-item" onclick={handleLogout}>Logout</button>
    <button
      class="nav-item"
      onclick={() => goto(`/profile/${$authStore.user?.username}`)}
    >
      Profile
    </button>
    <button class="nav-item" onclick={() => goto("/")}>Dashboard</button>
  </div>
  <NavButton {isOpen} onclick={toggle} />
</nav>

<style>
  .nav {
    position: fixed;
    bottom: 1rem;
    left: 1rem;
  }

  .nav-content {
    display: flex;
    flex-direction: column-reverse;
  }

  .nav-item {
    background-color: #333;
    border: none;
    color: white;
    border-radius: 1000px;
    height: 3rem;
    padding: 0 1rem;
    margin-bottom: 0.5rem;
    opacity: 1;
    transform: translateY(0);
    transition: opacity 0.3s ease, transform 0.3s ease, max-width 0.3s ease;
  }

  .closed .nav-item {
    opacity: 0;
    width: 3rem;
    transform: translateY(10px);
  }
</style>
