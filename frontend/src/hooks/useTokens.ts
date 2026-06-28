import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { tokensApi } from "../api/tokens";

export function useTokens() {
  return useQuery({
    queryKey: ["tokens"],
    queryFn: tokensApi.list,
  });
}

export function useCreateToken() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: tokensApi.create,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tokens"] }),
  });
}

export function useDeleteToken() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: tokensApi.delete,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["tokens"] }),
  });
}
