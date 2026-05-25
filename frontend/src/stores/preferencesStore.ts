import { create } from "zustand";
import { persist } from "zustand/middleware";

interface PreferencesState {
  autoLabelOnRead: boolean;
  setAutoLabelOnRead: (v: boolean) => void;
}

export const usePreferencesStore = create<PreferencesState>()(
  persist(
    (set) => ({
      autoLabelOnRead: false,
      setAutoLabelOnRead: (v) => set({ autoLabelOnRead: v }),
    }),
    { name: "harmonic-phoenix-prefs" }
  )
);
