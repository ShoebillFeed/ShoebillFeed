import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { sourcesApi } from "../api/sources";
import type { SourceCreate, SourceUpdate } from "../types/source";

export function useSources() {
  return useQuery({ queryKey: ["sources"], queryFn: sourcesApi.list });
}

export function useCreateSource() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: SourceCreate) => sourcesApi.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sources"] }),
  });
}

export function useUpdateSource() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: SourceUpdate }) => sourcesApi.update(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sources"] }),
  });
}

export function useDeleteSource() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: sourcesApi.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["sources"] }),
  });
}

export function useFetchSource() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: sourcesApi.fetch,
    onSuccess: () => setTimeout(() => qc.invalidateQueries({ queryKey: ["news"] }), 3000),
  });
}
