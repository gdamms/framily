import { writable, type Writable } from "svelte/store";

export type DashboardPage = {
  page: "dashboard";
}

export type FramiliesPage = {
  // The framilies of the user.
  page: "framilies";
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

export type PicturePage = {
  page: "picture";
  id: string;
}

export type Page = DashboardPage | FramiliesPage | ProfilePage | FramilyPage | PicturePage;

interface AppState {
  page: Page;
}

interface App {
  state: Writable<AppState>;
  navigate: (page: Page) => void;
}

function createApp(): App {
  const state: Writable<AppState> = writable({
    page: { page: "dashboard" },
  });

  function navigate(page: Page) {
    state.update(() => ({ page }));
  }

  return {
    state,
    navigate,
  };
}

export const app = createApp();
