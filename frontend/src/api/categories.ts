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
  // Runs as a Celery task rather than inline: this call kicks it off and returns a
  // task_id immediately; poll generatePromptResult until it's done. Keeps a slow/
  // unresponsive LLM from ever blocking a web request.
  generatePrompt: (name: string, keywords: string[], max_chars = 500, existing_categories: string[] = []) =>
    client
      .post<{ task_id: string }>("/categories/generate-prompt", { name, keywords, max_chars, existing_categories })
      .then((r) => r.data.task_id),
  generatePromptResult: (taskId: string) =>
    client
      .get<{ status: "pending" } | { status: "done"; prompt: string }>(`/categories/generate-prompt/${taskId}`)
      .then((r) => r.data),
  setManualWeight: (id: string, manual_weight: number) =>
    client.patch<Category>(`/categories/${id}/weight`, { manual_weight }).then((r) => r.data),
  export: () => client.get<CategoryExportItem[]>("/categories/export").then((r) => r.data),
  import: (data: CategoryExportItem[]) =>
    client.post<Category[]>("/categories/import", data).then((r) => r.data),
};
