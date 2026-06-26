import { create } from "zustand";
import { persist } from "zustand/middleware";
import i18n from "../i18n";

export type Theme = "light" | "dark";

function systemTheme(): Theme {
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

interface PreferencesState {
  theme: Theme;
  setTheme: (t: Theme) => void;
  uiLocale: string | null;
  setUiLocale: (locale: string | null) => void;
}

export const usePreferencesStore = create<PreferencesState>()(
  persist(
    (set) => ({
      theme: systemTheme(),
      setTheme: (t) => set({ theme: t }),
      uiLocale: null,
      setUiLocale: (locale) => {
        set({ uiLocale: locale });
        if (locale === null) {
          const browserLang = navigator.language.split("-")[0];
          i18n.changeLanguage(browserLang);
        } else {
          i18n.changeLanguage(locale);
        }
      },
    }),
    { name: "shoebill-feed-prefs" }
  )
);
