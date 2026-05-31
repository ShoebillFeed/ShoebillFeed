export type TabSort = "newest" | "relevant" | "impact";

export interface UserTab {
  id: string;
  name: string;
  sort: TabSort;
  category_ids: string[];
  source_ids: string[];
  unread_only: boolean;
  position: number;
}

export interface UserTabCreate {
  name: string;
  sort: TabSort;
  category_ids: string[];
  source_ids: string[];
  unread_only: boolean;
}

export interface UserTabUpdate {
  name?: string;
  sort?: TabSort;
  category_ids?: string[];
  source_ids?: string[];
  unread_only?: boolean;
}
