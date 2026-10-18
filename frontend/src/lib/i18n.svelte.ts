import {
  baseLocale,
  getLocale,
  isLocale,
  locales,
  overwriteGetLocale,
  setLocale,
  type Locale,
} from "$lib/paraglide/runtime";

export { m } from "$lib/paraglide/messages";
export { locales, type Locale };

// Each language is labelled in its own language, so people can always find
// theirs whatever the current UI language is.
export const LANGUAGE_NAMES: Record<Locale, string> = {
  en: "English",
  fr: "Français",
};

function resolveInitialLocale(): Locale {
  try {
    // Paraglide's strategy: stored choice, then browser language, then English.
    return getLocale();
  } catch {
    return baseLocale;
  }
}

// Mirror the locale into a rune so every `m.*()` call made from a template
// re-renders when it changes. This app is client-only (see +layout.ts), so
// switching languages in place is fine and avoids a full page reload.
let current = $state<Locale>(resolveInitialLocale());
overwriteGetLocale(() => current);
applyDocumentLang(current);

function applyDocumentLang(locale: Locale): void {
  if (typeof document !== "undefined") {
    document.documentElement.lang = locale;
  }
}

export function getLanguage(): Locale {
  return current;
}

/** Switch the UI language. Ignores values that aren't a supported locale. */
export function setLanguage(locale: string | null | undefined): void {
  if (!isLocale(locale) || locale === current) return;
  try {
    // Persists the choice to localStorage (the only stateful strategy we use).
    setLocale(locale, { reload: false });
  } catch {
    // Storage unavailable (e.g. private browsing) - still switch for this session.
  }
  current = locale;
  applyDocumentLang(locale);
}
