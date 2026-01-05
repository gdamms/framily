<script lang="ts">
  import { goto } from '$app/navigation';
  import { authStore } from '$lib/stores/auth';
  import { api } from '$lib/api';

  let isLoading = false;

  const handleLogout = async () => {
    isLoading = true;
    try {
      const token = authStore.getToken();
      if (token) {
        await api.auth.logout(token);
      }
      authStore.clearToken();
      await goto('/login');
    } catch (error) {
      console.error('Logout error:', error);
      // Clear token anyway on error
      authStore.clearToken();
      await goto('/login');
    } finally {
      isLoading = false;
    }
  };
</script>

<div class="logout-container">
  <button on:click={handleLogout} disabled={isLoading}>
    {isLoading ? 'Logging out...' : 'Logout'}
  </button>
</div>

<style>
  .logout-container {
    display: flex;
    justify-content: center;
    margin-top: 2rem;
  }

  button {
    padding: 0.5rem 1rem;
    background-color: #dc2626;
    color: white;
    border: none;
    border-radius: 4px;
    cursor: pointer;
    font-size: 1rem;
  }

  button:hover:not(:disabled) {
    background-color: #b91c1c;
  }

  button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
</style>
