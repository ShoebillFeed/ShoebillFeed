import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { categoriesApi } from "../api/categories";
import type { CategoryCreate, CategoryUpdate } from "../types/category";

export function useCategories() {
  return useQuery({ queryKey: ["categories"], queryFn: categoriesApi.list });
}

export function useCreateCategory() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: CategoryCreate) => categoriesApi.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["categories"] }),
  });
}

export function useUpdateCategory() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: CategoryUpdate }) => categoriesApi.update(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["categories"] }),
  });
}

export function useDeleteCategory() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: categoriesApi.delete,
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ["categories"] });
      qc.invalidateQueries({ queryKey: ["news"] });
    },
  });
}

export function useResetWeights() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: categoriesApi.resetWeights,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["categories"] }),
  });
}

export function useSetManualWeight() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, manual_weight }: { id: string; manual_weight: number }) =>
      categoriesApi.setManualWeight(id, manual_weight),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["categories"] }),
  });
}
