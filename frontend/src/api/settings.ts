import client from "./client";

export interface UserSettings {
  weight_base: number;
  weight_log_multiplier: number;
  relevance_llm_weight: number;
  relevance_learning_weight: number;
  relevance_cluster_weight: number;
  stats_enabled: boolean;
  output_language: string | null;
  time_decay_param: number;
  show_decay_param: number;
  mark_shown_delay_seconds: number;
  learning_window_days: number;
  ignore_penalty_weight: number;
  push_enabled: boolean;
  push_min_relevance: number;
  push_top_category_percent: number;
  push_all_categories: boolean;
  push_category_ids: string[];
  push_all_sources: boolean;
  push_source_ids: string[];
  push_cluster_per_source: boolean;
  push_all_tabs: boolean;
  push_tab_ids: string[];
}

export interface UserSettingsUpdate {
  weight_base?: number;
  weight_log_multiplier?: number;
  relevance_llm_weight?: number;
  relevance_learning_weight?: number;
  relevance_cluster_weight?: number;
  stats_enabled?: boolean;
  output_language?: string | null;
  time_decay_param?: number;
  show_decay_param?: number;
  mark_shown_delay_seconds?: number;
  learning_window_days?: number;
  ignore_penalty_weight?: number;
  push_enabled?: boolean;
  push_min_relevance?: number;
  push_top_category_percent?: number;
  push_all_categories?: boolean;
  push_category_ids?: string[];
  push_all_sources?: boolean;
  push_source_ids?: string[];
  push_cluster_per_source?: boolean;
  push_all_tabs?: boolean;
  push_tab_ids?: string[];
}

export const settingsApi = {
  getAdvanced: () => client.get<UserSettings>("/settings/advanced").then((r) => r.data),
  updateAdvanced: (data: UserSettingsUpdate) =>
    client.patch<UserSettings>("/settings/advanced", data).then((r) => r.data),
};
