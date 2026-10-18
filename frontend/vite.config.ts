import { paraglideVitePlugin } from '@inlang/paraglide-js';
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
	plugins: [
		paraglideVitePlugin({
			project: './project.inlang',
			outdir: './src/lib/paraglide',
			// Client-only SPA without localized URLs: the stored choice wins, then
			// the browser language, then English.
			strategy: ['localStorage', 'preferredLanguage', 'baseLocale'],
		}),
		sveltekit(),
	],
	server: {
		allowedHosts: [getAllowedHost()],
	},
});

function getAllowedHost() {
	const url = process.env.ALLOWED_HOST;
	return url ? url : 'localhost';
}
