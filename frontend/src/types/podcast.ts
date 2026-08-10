export interface PodcastHost {
  id: string;
  name: string;
  character_prompt: string;
  voice: string;
  // Chatterbox-specific emotion/delivery intensity (null = engine default).
  // Has no effect on Piper/Kokoro -- only shown in the form when the
  // configured TTS engine reports supports_exaggeration.
  exaggeration?: number | null;
  // Pins this host to a specific engine instead of the deployment's global
  // default (null = use the default). "network" only works when the
  // backend reports network_configured.
  tts_provider?: "piper" | "network" | null;
}

export interface PodcastShow {
  id: string;
  name: string;
  description: string | null;
  hosts: PodcastHost[];
  category_ids: string[];
  source_ids: string[];
  time_window_hours: number;
  target_length_minutes: number;
  language: string;
  schedule_time: string;
  timezone: string;
  speech_rate: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  public_feed_enabled: boolean;
  public_feed_url: string | null;
  cover_image_url: string | null;
}

export interface PodcastShowCreate {
  name: string;
  description?: string | null;
  hosts: PodcastHost[];
  category_ids: string[];
  source_ids: string[];
  time_window_hours: number;
  target_length_minutes: number;
  language: string;
  schedule_time: string;
  timezone: string;
  speech_rate: number;
  is_active: boolean;
}

export interface PodcastShowUpdate {
  name?: string;
  description?: string | null;
  hosts?: PodcastHost[];
  category_ids?: string[];
  source_ids?: string[];
  time_window_hours?: number;
  target_length_minutes?: number;
  language?: string;
  schedule_time?: string;
  timezone?: string;
  speech_rate?: number;
  is_active?: boolean;
}

export type PodcastEpisodeStatus = "pending" | "generating" | "ready" | "failed";

export interface PodcastScriptTurn {
  host_id: string;
  // Absent on episodes generated before this field existed.
  host_name: string | null;
  story_index: number | null;
  text: string;
}

export interface PodcastShownote {
  title: string;
  source_name: string;
  url: string | null;
  start_seconds: number;
}

export interface PodcastEpisode {
  id: string;
  show_id: string;
  show_name: string;
  show_cover_image_url: string | null;
  status: PodcastEpisodeStatus;
  script: PodcastScriptTurn[] | null;
  shownotes: PodcastShownote[] | null;
  description: string;
  news_item_ids: string[];
  news_cluster_ids: string[];
  duration_seconds: number | null;
  error_message: string | null;
  created_at: string;
  generated_at: string | null;
}

export interface PodcastEpisodePage {
  items: PodcastEpisode[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface PodcastVoice {
  id: string;
  label: string;
}
