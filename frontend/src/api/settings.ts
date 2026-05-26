import client from "./client";

export interface UserSettings {
  weight_base: number;
  weight_log_multiplier: number;
  relevance_llm_weight: number;
  relevance_learning_weight: number;
  relevance_cluster_weight: number;
  stats_enabled: boolean;
}

export interface UserSettingsUpdate {
  weight_base?: number;
  weight_log_multiplier?: number;
  relevance_llm_weight?: number;
  relevance_learning_weight?: number;
  relevance_cluster_weight?: number;
  stats_enabled?: boolean;
}

export const settingsApi = {
  getAdvanced: () => client.get<UserSettings>("/settings/advanced").then((r) => r.data),
  updateAdvanced: (data: UserSettingsUpdate) =>
    client.patch<UserSettings>("/settings/advanced", data).then((r) => r.data),
};
