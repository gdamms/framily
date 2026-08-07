import { writable, get } from "svelte/store";

export type ThemePreference = "system" | "light" | "dark";
export type ResolvedTheme = "light" | "dark";

const STORAGE_KEY = "framily:theme";

function isThemePreference(value: unknown): value is ThemePreference {
  return value === "system" || value === "light" || value === "dark";
}

function loadStoredPreference(): ThemePreference {
  if (typeof localStorage === "undefined") {
    return "system";
  }
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    return isThemePreference(raw) ? raw : "system";
  } catch {
    return "system";
  }
}

function storePreference(preference: ThemePreference): void {
  if (typeof localStorage === "undefined") {
    return;
  }
  try {
    localStorage.setItem(STORAGE_KEY, preference);
  } catch {
    // Storage unavailable (e.g. private browsing quota) - ignore.
  }
}

function getSystemTheme(): ResolvedTheme {
  if (typeof window === "undefined") {
    return "light";
  }
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

function resolveTheme(preference: ThemePreference): ResolvedTheme {
  return preference === "system" ? getSystemTheme() : preference;
}

function applyResolvedTheme(theme: ResolvedTheme): void {
  if (typeof document !== "undefined") {
    document.documentElement.dataset.theme = theme;
  }
}

function createThemeStore() {
  const initialPreference = loadStoredPreference();

  const preference = writable<ThemePreference>(initialPreference);
  const resolved = writable<ResolvedTheme>(resolveTheme(initialPreference));

  function sync() {
    const value = resolveTheme(get(preference));
    resolved.set(value);
    applyResolvedTheme(value);
  }

  sync();

  if (typeof window !== "undefined") {
    window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
      if (get(preference) === "system") {
        sync();
      }
    });
  }

  function setPreference(next: ThemePreference): void {
    preference.set(next);
    storePreference(next);
    sync();
  }

  function cycle(): void {
    const order: ThemePreference[] = ["system", "light", "dark"];
    const next = order[(order.indexOf(get(preference)) + 1) % order.length];
    setPreference(next);
  }

  return {
    preference: { subscribe: preference.subscribe },
    resolved: { subscribe: resolved.subscribe },
    setPreference,
    cycle,
  };
}

export const themeStore = createThemeStore();
