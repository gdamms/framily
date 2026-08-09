import { authStore } from "$lib/stores/auth";
import { serverUrlStore } from "$lib/stores/serverUrl";

// The auth cookie only exists client-side (read directly from `document.cookie`,
// see `$lib/stores/auth.ts`), so server-rendering this app produces a shell
// that's always logged-out and gets swapped out right after hydration - a
// visible flash of the login form on every reload. Render client-only instead.
export const ssr = false;

// On native, both stores hydrate from Capacitor Preferences asynchronously
// and independently. Without waiting here, the very first API call (e.g. the
// bootstrap `loadApp()` in +page.svelte on cold start) could fire before
// serverUrlStore has loaded, resolve against an empty base URL, fail, and
// get stuck - see the `ready` promises in stores/auth.ts and
// stores/serverUrl.ts.
export async function load() {
  await Promise.all([authStore.ready, serverUrlStore.ready]);
}
