import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { tabsApi } from "../api/tabs";
import type { UserTabCreate, UserTabUpdate } from "../types/tabs";

export function useUserTabs() {
  return useQuery({ queryKey: ["tabs"], queryFn: tabsApi.list });
}

export function useCreateTab() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: UserTabCreate) => tabsApi.create(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tabs"] }),
  });
}

export function useUpdateTab() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, data }: { id: string; data: UserTabUpdate }) => tabsApi.update(id, data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tabs"] }),
  });
}

export function useDeleteTab() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) => tabsApi.delete(id),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tabs"] }),
  });
}
