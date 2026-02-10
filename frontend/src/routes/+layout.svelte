<script lang="ts">
  import favicon from "$lib/assets/favicon.svg";
  import { authStore } from "$lib/stores/auth";
  import { goto } from "$app/navigation";

  let { children } = $props();

  const handleLogout = () => {
    authStore.clearToken();
    goto("/login");
  };
</script>

<svelte:head>
  <link rel="icon" href={favicon} />
</svelte:head>

<nav>
  <div class="nav-brand">
    <a href="/">Framily</a>
  </div>
  <div class="nav-links">
    {#if $authStore.isAuthenticated}
      <a href="/">Dashboard</a>
      <span class="user-info">
        {$authStore.user?.display_name}
      </span>
      <button onclick={handleLogout} class="logout-btn">Logout</button>
    {:else}
      <a href="/login">Login</a>
      <a href="/register">Register</a>
    {/if}
  </div>
</nav>

<main>
  {@render children()}
</main>

<style>
  :global(body) {
    margin: 0;
    padding: 0;
    font-family: Arial, sans-serif;
    background-color: #f5f5f5;
    height: 100vh;
    display: flex;
    flex-direction: column;
  }

  nav {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem 2rem;
    background-color: #333;
    color: white;
  }

  main {
    flex: 1;
  }
</style>
