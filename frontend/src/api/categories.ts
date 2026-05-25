import client from "./client";
import type { Category, CategoryCreate, CategoryUpdate } from "../types/category";

export const categoriesApi = {
  list: () => client.get<Category[]>("/categories").then((r) => r.data),
  create: (data: CategoryCreate) => client.post<Category>("/categories", data).then((r) => r.data),
  update: (id: string, data: CategoryUpdate) =>
    client.patch<Category>(`/categories/${id}`, data).then((r) => r.data),
  delete: (id: string) => client.delete(`/categories/${id}`),
  resetWeights: () => client.post("/categories/reset-weights").then((r) => r.data),
  generatePrompt: (name: string, keywords: string[]) =>
    client
      .post<{ prompt: string }>("/categories/generate-prompt", { name, keywords })
      .then((r) => r.data.prompt),
  setManualWeight: (id: string, manual_weight: number) =>
    client.patch<Category>(`/categories/${id}/weight`, { manual_weight }).then((r) => r.data),
};
