import { create } from "zustand";
import type { FeedTab } from "../types/news";

interface FilterState {
  activeTab: FeedTab;
  activeCustomTabId: string | null;
  selectedCategoryIds: string[];
  selectedSourceIds: string[];
  showUnreadOnly: boolean;
  showUncategorizedOnly: boolean;
  categoryFilterExpanded: boolean;
  sourceFilterExpanded: boolean;
  setTab: (tab: FeedTab) => void;
  setCustomTab: (id: string | null) => void;
  toggleCategory: (id: string) => void;
  clearCategories: () => void;
  toggleSource: (id: string) => void;
  clearSources: () => void;
  setShowUnreadOnly: (v: boolean) => void;
  setShowUncategorizedOnly: (v: boolean) => void;
  setCategoryFilterExpanded: (v: boolean) => void;
  setSourceFilterExpanded: (v: boolean) => void;
}

export const useFilterStore = create<FilterState>((set) => ({
  activeTab: "newest",
  activeCustomTabId: null,
  selectedCategoryIds: [],
  selectedSourceIds: [],
  showUnreadOnly: false,
  showUncategorizedOnly: false,
  categoryFilterExpanded: false,
  sourceFilterExpanded: false,
  setTab: (tab) => set({ activeTab: tab, activeCustomTabId: null }),
  setCustomTab: (id) => set({ activeCustomTabId: id }),
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
  setShowUncategorizedOnly: (v) => set({ showUncategorizedOnly: v }),
  setCategoryFilterExpanded: (v) => set({ categoryFilterExpanded: v }),
  setSourceFilterExpanded: (v) => set({ sourceFilterExpanded: v }),
}));
