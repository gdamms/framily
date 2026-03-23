import { writable } from 'svelte/store';

type Theme = 'light' | 'dark';

function createThemeStore() {
  const storedTheme = typeof window !== 'undefined'
    ? localStorage.getItem('theme') as Theme | null
    : null;

  const { subscribe, set } = writable<Theme>(storedTheme || 'light');

  return {
    subscribe,
    setTheme: (theme: Theme) => {
      localStorage.setItem('theme', theme);
      set(theme);
      document.documentElement.classList.toggle('dark', theme === 'dark');
    },
    toggle: () => {
      let currentTheme: Theme;
      const unsubscribe = subscribe(theme => currentTheme = theme);
      unsubscribe();

      const newTheme = currentTheme === 'light' ? 'dark' : 'light';
      themeStore.setTheme(newTheme);
    }
  };
}

export const themeStore = createThemeStore();
