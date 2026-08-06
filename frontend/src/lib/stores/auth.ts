import { writable } from "svelte/store";

const AUTH_COOKIE_NAME = "auth_token";

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
    typeof window !== "undefined" ? getAuthTokenFromCookie() : null;

  const authState = writable<AuthState>({
    token: initialToken,
    isAuthenticated: !!initialToken,
    isLoading: !!initialToken,
  });

  const resetAuthState = () => {
    clearAuthTokenCookie();
    authState.set({
      token: null,
      isAuthenticated: false,
      isLoading: false,
    });
  };

  return {
    subscribe: authState.subscribe,
    set: authState.set,
    update: authState.update,
    setToken: async (token: string, rememberMe: boolean = true) => {
      setAuthTokenCookie(token, rememberMe);
      authState.update((state) => ({
        ...state,
        token,
        isAuthenticated: true,
        isLoading: true,
      }));

      try {
        authState.update((state) => ({ ...state, isLoading: false }));
      } catch {
        clearAuthTokenCookie();
        resetAuthState();
      }
    },
    clearToken: () => {
      clearAuthTokenCookie();
      resetAuthState();
    },
    getToken: (): string | null => {
      if (typeof window !== "undefined") {
        return getAuthTokenFromCookie();
      }
      return null;
    },
  };
}

export const authStore = createAuthStore();
