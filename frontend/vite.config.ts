import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [sveltekit()],
	server: {
		allowedHosts: [getAllowedHost()],
	},
});

function getAllowedHost() {
	const url = process.env.ALLOWED_HOST;
	return url ? url : 'localhost';
}
