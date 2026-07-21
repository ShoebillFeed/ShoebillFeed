export type TabSort = "newest" | "relevant" | "impact";

// Keep in sync with backend/app/api/tabs.py's TAB_ICONS.
export const TAB_ICON_NAMES = [
  "star", "heart", "flag", "globe", "compass", "flame", "rocket", "coffee",
  "home", "briefcase", "music", "camera", "gamepad2", "sparkles", "trophy",
  "lightbulb", "gift", "graduationcap", "mic", "rss", "layers", "mappin",
  "leaf", "pawprint",
] as const;

export type TabIconName = (typeof TAB_ICON_NAMES)[number];

export interface UserTab {
  id: string;
  name: string;
  sort: TabSort;
  category_ids: string[];
  source_ids: string[];
  unread_only: boolean;
  position: number;
  icon: TabIconName | null;
}

export interface UserTabCreate {
  name: string;
  sort: TabSort;
  category_ids: string[];
  source_ids: string[];
  unread_only: boolean;
  icon?: TabIconName | null;
}

export interface UserTabUpdate {
  name?: string;
  sort?: TabSort;
  category_ids?: string[];
  source_ids?: string[];
  unread_only?: boolean;
  icon?: TabIconName | null;
}
