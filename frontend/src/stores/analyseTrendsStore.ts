import { create } from "zustand";
import { persist } from "zustand/middleware";

export interface TrendTopicConfig {
  id: string;
  label: string;
  keywords: string[];
}

interface AnalyseTrendsState {
  topics: TrendTopicConfig[];
  categoryIds: string[];
  sourceIds: string[];
  days: number | null;
  setTopics: (topics: TrendTopicConfig[]) => void;
  setCategoryIds: (ids: string[]) => void;
  setSourceIds: (ids: string[]) => void;
  setDays: (days: number | null) => void;
}

// Persisted so a user's configured topics/filters/range survive a reload or
// navigating away from the Trends tab -- otherwise every visit meant
// re-typing keywords from scratch. Local to the browser (like
// preferencesStore's theme), not synced across devices.
export const useAnalyseTrendsStore = create<AnalyseTrendsState>()(
  persist(
    (set) => ({
      topics: [],
      categoryIds: [],
      sourceIds: [],
      days: 90,
      setTopics: (topics) => set({ topics }),
      setCategoryIds: (categoryIds) => set({ categoryIds }),
      setSourceIds: (sourceIds) => set({ sourceIds }),
      setDays: (days) => set({ days }),
    }),
    { name: "shoebill-feed-trends" }
  )
);
