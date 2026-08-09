import { writable } from "svelte/store";
import { Capacitor } from "@capacitor/core";
import { Preferences } from "@capacitor/preferences";

const AUTH_COOKIE_NAME = "auth_token";
const AUTH_TOKEN_KEY = "auth_token";
// Cookies are scoped to the app's own origin, which never matches a
// self-hosted backend's origin in the packaged app - so native builds use
// Preferences + a Bearer header (see api/client.ts) instead of a cookie.
const isNative = Capacitor.isNativePlatform();

export interface AuthState {
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

function getAuthTokenFromCookie(): string | null {
  if (typeof document === "undefined") {
    return null;
  }

  const cookiePrefix = `${AUTH_COOKIE_NAME}=`;
  const cookie = document.cookie
    .split(";")
    .map((value) => value.trim())
    .find((value) => value.startsWith(cookiePrefix));

  if (!cookie) {
    return null;
  }

  return decodeURIComponent(cookie.slice(cookiePrefix.length));
}

function setAuthTokenCookie(token: string, persist: boolean): void {
  if (typeof document === "undefined") {
    return;
  }

  const secureFlag = window.location.protocol === "https:" ? "; Secure" : "";
  // Persistent ("stay logged in"): a long-lived cookie matching the
  // infinite-expiry token from the backend. Otherwise: a session cookie
  // (no Max-Age) so it's cleared when the browser closes, matching the
  // short-lived token issued in that case.
  const maxAge = persist ? "; Max-Age=315360000" : "";
  document.cookie = `${AUTH_COOKIE_NAME}=${encodeURIComponent(token)}; Path=/${maxAge}; SameSite=Lax${secureFlag}`;
}

function clearAuthTokenCookie(): void {
  if (typeof document === "undefined") {
    return;
  }

  const secureFlag = window.location.protocol === "https:" ? "; Secure" : "";
  document.cookie = `${AUTH_COOKIE_NAME}=; Path=/; Max-Age=0; SameSite=Lax${secureFlag}`;
}

function createAuthStore() {
  const initialToken =
    !isNative && typeof window !== "undefined" ? getAuthTokenFromCookie() : null;

  const authState = writable<AuthState>({
    token: initialToken,
    isAuthenticated: !!initialToken,
    // Native: token isn't known synchronously, Preferences.get resolves below.
    isLoading: isNative || !!initialToken,
  });

  // Awaited by +layout.ts before the app renders anything that could fetch -
  // see the matching comment in stores/serverUrl.ts.
  const ready: Promise<void> = isNative
    ? Preferences.get({ key: AUTH_TOKEN_KEY }).then(({ value }) => {
        authState.update((state) => ({
          ...state,
          token: value,
          isAuthenticated: !!value,
          isLoading: false,
        }));
      })
    : Promise.resolve();

  const resetAuthState = () => {
    if (isNative) {
      void Preferences.remove({ key: AUTH_TOKEN_KEY });
    } else {
      clearAuthTokenCookie();
    }
    authState.set({
      token: null,
      isAuthenticated: false,
      isLoading: false,
    });
  };

  return {
    subscribe: authState.subscribe,
    ready,
    set: authState.set,
    update: authState.update,
    setToken: async (token: string, rememberMe: boolean = true) => {
      if (isNative) {
        await Preferences.set({ key: AUTH_TOKEN_KEY, value: token });
      } else {
        setAuthTokenCookie(token, rememberMe);
      }
      authState.update((state) => ({
        ...state,
        token,
        isAuthenticated: true,
        isLoading: false,
      }));
    },
    clearToken: () => {
      resetAuthState();
    },
    getToken: (): string | null => {
      if (!isNative && typeof window !== "undefined") {
        return getAuthTokenFromCookie();
      }
      return null;
    },
  };
}

export const authStore = createAuthStore();
