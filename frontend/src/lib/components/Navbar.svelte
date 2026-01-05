<script lang="ts">
  import { authStore } from '$lib/stores/auth';
  import LogoutButton from '$lib/components/LogoutButton.svelte';

  let isAuthenticated = false;

  authStore.subscribe((state) => {
    isAuthenticated = state.isAuthenticated;
  });
</script>

<nav class="navbar">
  <div class="nav-content">
    <h1>Framily</h1>
    {#if isAuthenticated}
      <LogoutButton />
    {/if}
  </div>
</nav>

<style>
  .navbar {
    background-color: #1f2937;
    color: white;
    padding: 1rem 0;
  }

  .nav-content {
    max-width: 1200px;
    margin: 0 auto;
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 1rem;
  }

  h1 {
    margin: 0;
    font-size: 1.5rem;
  }
</style>
