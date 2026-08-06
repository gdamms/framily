// The auth cookie only exists client-side (read directly from `document.cookie`,
// see `$lib/stores/auth.ts`), so server-rendering this app produces a shell
// that's always logged-out and gets swapped out right after hydration - a
// visible flash of the login form on every reload. Render client-only instead.
export const ssr = false;
