export interface CategoryWeight {
  weight: number;
  manual_weight: number;
  total_marked: number;
}

export interface Category {
  id: string;
  name: string;
  color: string;
  keywords: string[];
  prompt: string | null;
  taxonomy_id: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  weight: CategoryWeight | null;
  item_count: number;
}

export interface CategoryCreate {
  name: string;
  color: string;
  keywords: string[];
  prompt?: string | null;
  taxonomy_id?: string | null;
}

export interface CategoryUpdate {
  name?: string;
  color?: string;
  keywords?: string[];
  prompt?: string | null;
  is_active?: boolean;
}
