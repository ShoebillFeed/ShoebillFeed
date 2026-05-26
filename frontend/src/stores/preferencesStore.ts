import { create } from "zustand";
import { persist } from "zustand/middleware";

export type Theme = "light" | "dark";

function systemTheme(): Theme {
  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

interface PreferencesState {
  autoLabelOnRead: boolean;
  setAutoLabelOnRead: (v: boolean) => void;
  theme: Theme;
  setTheme: (t: Theme) => void;
}

export const usePreferencesStore = create<PreferencesState>()(
  persist(
    (set) => ({
      autoLabelOnRead: true,
      setAutoLabelOnRead: (v) => set({ autoLabelOnRead: v }),
      theme: systemTheme(),
      setTheme: (t) => set({ theme: t }),
    }),
    { name: "shoebill-feed-prefs" }
  )
);
