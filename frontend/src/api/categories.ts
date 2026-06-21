import client from "./client";
import type { Category, CategoryCreate, CategoryUpdate } from "../types/category";

export interface CategoryExportItem {
  name: string;
  color: string;
  keywords: string[];
  prompt: string | null;
  taxonomy_id?: string | null;
}

export const categoriesApi = {
  list: (sourceIds?: string[]) =>
    client.get<Category[]>("/categories", {
      params: sourceIds?.length ? { source_ids: sourceIds } : undefined,
      paramsSerializer: { indexes: null },
    }).then((r) => r.data),
  create: (data: CategoryCreate) => client.post<Category>("/categories", data).then((r) => r.data),
  update: (id: string, data: CategoryUpdate) =>
    client.patch<Category>(`/categories/${id}`, data).then((r) => r.data),
  delete: (id: string) => client.delete(`/categories/${id}`),
  resetWeights: () => client.post("/categories/reset-weights").then((r) => r.data),
  generatePrompt: (name: string, keywords: string[], max_chars = 500) =>
    client
      .post<{ prompt: string }>("/categories/generate-prompt", { name, keywords, max_chars }, { timeout: 120_000 })
      .then((r) => r.data.prompt),
  setManualWeight: (id: string, manual_weight: number) =>
    client.patch<Category>(`/categories/${id}/weight`, { manual_weight }).then((r) => r.data),
  export: () => client.get<CategoryExportItem[]>("/categories/export").then((r) => r.data),
  import: (data: CategoryExportItem[]) =>
    client.post<Category[]>("/categories/import", data).then((r) => r.data),
};
