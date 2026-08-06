import { writable, type Writable } from "svelte/store";

export type DashboardPage = {
  page: "dashboard";
  section: "galery" | "framilies";
}

export type ProfilePage = {
  page: "profile";
  username: string;
  section: "pictures" | "framilies" | "settings";
}

export type FramilyPage = {
  page: "framily";
  code: string;
  section: "pictures" | "members" | "settings";
}

export type Page = DashboardPage | ProfilePage | FramilyPage;

export type AuthView = "login" | "register";

interface AppState {
  page: Page;
}

interface App {
  state: Writable<AppState>;
  navigate: (page: Page) => void;
}

// Which unauthenticated screen to show. Not persisted: on every load we want
// to start from the login form, and it's reset once the user is authenticated.
export const authView: Writable<AuthView> = writable("login");

const STORAGE_KEY = "framily:page";
const DEFAULT_PAGE: Page = { page: "dashboard", section: "galery" };

function loadStoredPage(): Page {
  if (typeof localStorage === "undefined") {
    return DEFAULT_PAGE;
  }

  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) {
      return DEFAULT_PAGE;
    }
    const parsed = JSON.parse(raw);
    if (parsed && typeof parsed.page === "string") {
      return parsed as Page;
    }
  } catch {
    // Malformed or inaccessible storage - fall back to the default page.
  }
  return DEFAULT_PAGE;
}

function storePage(page: Page): void {
  if (typeof localStorage === "undefined") {
    return;
  }
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(page));
  } catch {
    // Storage unavailable (e.g. private browsing quota) - ignore.
  }
}

function createApp(): App {
  const state: Writable<AppState> = writable({
    page: loadStoredPage(),
  });

  function navigate(page: Page) {
    state.update(() => ({ page }));
    storePage(page);
  }

  return {
    state,
    navigate,
  };
}

export const app = createApp();
