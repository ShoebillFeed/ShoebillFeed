export interface CategorySummary {
  id: string;
  name: string;
  color: string;
}

export interface SourceSummary {
  id: string;
  name: string;
  source_type: string;
}

export interface NewsItem {
  kind: "item";
  id: string;
  title: string;
  url: string;
  abstract: string | null;
  extracted_keywords: string[] | null;
  image_url: string | null;
  relevance_score: number | null;
  impact_score: number | null;
  llm_processed: boolean;
  is_read: boolean;
  is_relevant: boolean;
  read_later: boolean;
  published_at: string | null;
  fetched_at: string;
  source: SourceSummary | null;
  categories: CategorySummary[];
}

export interface ClusterItem {
  id: string;
  title: string;
  url: string;
  image_url: string | null;
  source_summary: string | null;
  fetched_at: string;
  source: SourceSummary | null;
}

export interface NewsCluster {
  kind: "cluster";
  id: string;
  title: string | null;
  unified_abstract: string | null;
  extracted_keywords: string[] | null;
  relevance_score: number | null;
  impact_score: number | null;
  is_read: boolean;
  last_read_at: string | null;
  is_relevant: boolean;
  read_later: boolean;
  llm_processed: boolean;
  published_at: string | null;
  categories: CategorySummary[];
  items: ClusterItem[];
}

export type FeedEntry = NewsItem | NewsCluster;

export type FeedTab = "newest" | "relevant" | "impact" | "read_later";

export interface NewsPage {
  items: FeedEntry[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}
