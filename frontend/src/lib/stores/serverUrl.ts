import { writable } from "svelte/store";
import { Capacitor } from "@capacitor/core";
import { Preferences } from "@capacitor/preferences";

const SERVER_URL_KEY = "server_url";
const isNative = Capacitor.isNativePlatform();

// Trailing-slash stripping happens only where the URL is consumed
// (normalizeServerUrl, used by api/client.ts), not in the store itself:
// normalizing on every keystroke fought the input field's own "//", since
// the in-progress trailing "/" while typing "https://" kept getting
// stripped right back off before the second "/" could be typed.
export function normalizeServerUrl(url: string): string {
  return url.trim().replace(/\/+$/, "");
}

function createServerUrlStore() {
  const store = writable<string>("");

  // Awaited by +layout.ts before the app renders anything that could fetch,
  // so getApiBaseUrl() never reads this store before it's hydrated (a request
  // fired mid-hydration would resolve against "" and fail outright).
  const ready: Promise<void> = isNative
    ? Preferences.get({ key: SERVER_URL_KEY }).then(({ value }) => {
        if (value) {
          store.set(value);
        }
      })
    : Promise.resolve();

  return {
    subscribe: store.subscribe,
    ready,
    // Kept in sync with Preferences on every write, independently of the
    // auth token, so it survives logout (unlike stores/auth.ts's token,
    // which is cleared there) - the point is the user shouldn't have to
    // retype their server address after signing out.
    set: (url: string) => {
      store.set(url);
      if (isNative) {
        void Preferences.set({ key: SERVER_URL_KEY, value: url });
      }
    },
  };
}

export const serverUrlStore = createServerUrlStore();
