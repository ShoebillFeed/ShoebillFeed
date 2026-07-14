export type SourceType = "rss" | "atom" | "reddit" | "email" | "mastodon" | "arxiv" | "lemmy" | "github" | "bluesky" | "telegram" | "scraper";

export interface Source {
  id: string;
  name: string;
  source_type: SourceType;
  config: Record<string, unknown>;
  is_active: boolean;
  fetch_interval: number;
  last_fetched_at: string | null;
  created_at: string;
  item_count: number;
}

export interface SourceCreate {
  name: string;
  source_type: SourceType;
  config: Record<string, unknown>;
  is_active: boolean;
  fetch_interval: number;
}

export interface SourceUpdate {
  name?: string;
  config?: Record<string, unknown>;
  is_active?: boolean;
  fetch_interval?: number;
}
