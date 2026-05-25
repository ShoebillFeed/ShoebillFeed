import { create } from "zustand";
import type { FeedTab } from "../types/news";

interface FilterState {
  activeTab: FeedTab;
  selectedCategoryIds: string[];
  selectedSourceIds: string[];
  showUnreadOnly: boolean;
  setTab: (tab: FeedTab) => void;
  toggleCategory: (id: string) => void;
  clearCategories: () => void;
  toggleSource: (id: string) => void;
  clearSources: () => void;
  setShowUnreadOnly: (v: boolean) => void;
}

export const useFilterStore = create<FilterState>((set) => ({
  activeTab: "newest",
  selectedCategoryIds: [],
  selectedSourceIds: [],
  showUnreadOnly: false,
  setTab: (tab) => set({ activeTab: tab }),
  toggleCategory: (id) =>
    set((s) => ({
      selectedCategoryIds: s.selectedCategoryIds.includes(id)
        ? s.selectedCategoryIds.filter((x) => x !== id)
        : [...s.selectedCategoryIds, id],
    })),
  clearCategories: () => set({ selectedCategoryIds: [] }),
  toggleSource: (id) =>
    set((s) => ({
      selectedSourceIds: s.selectedSourceIds.includes(id)
        ? s.selectedSourceIds.filter((x) => x !== id)
        : [...s.selectedSourceIds, id],
    })),
  clearSources: () => set({ selectedSourceIds: [] }),
  setShowUnreadOnly: (v) => set({ showUnreadOnly: v }),
}));
