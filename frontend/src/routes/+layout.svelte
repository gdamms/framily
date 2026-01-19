<script lang="ts">
	import favicon from '$lib/assets/favicon.svg';
	import { authStore } from '$lib/stores/auth';
	import { goto } from '$app/navigation';

	let { children } = $props();

	const handleLogout = () => {
		authStore.clearToken();
		goto('/login');
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
				{$authStore.user?.display_name || $authStore.user?.username || 'User'}
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
	}

	nav {
		display: flex;
		justify-content: space-between;
		align-items: center;
		padding: 1rem 2rem;
		background-color: #333;
		color: white;
	}

	.nav-brand a {
		color: white;
		text-decoration: none;
		font-size: 1.5rem;
		font-weight: bold;
	}

	.nav-links {
		display: flex;
		gap: 1rem;
		align-items: center;
	}

	.nav-links a {
		color: white;
		text-decoration: none;
		padding: 0.5rem 1rem;
	}

	.nav-links a:hover {
		background-color: #555;
		border-radius: 4px;
	}

	.user-info {
		color: #aaa;
	}

	.logout-btn {
		background-color: #dc3545;
		color: white;
		border: none;
		padding: 0.5rem 1rem;
		border-radius: 4px;
		cursor: pointer;
	}

	.logout-btn:hover {
		background-color: #c82333;
	}

	main {
		max-width: 1200px;
		margin: 0 auto;
		padding: 2rem 1rem;
	}
</style>
