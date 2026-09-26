import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { tokensApi } from "../api/tokens";

export function useTokens() {
  return useQuery({
    queryKey: ["tokens"],
    queryFn: tokensApi.list,
  });
}

export function useTokenScopes() {
  return useQuery({
    queryKey: ["tokens", "scopes"],
    queryFn: tokensApi.scopes,
    // The scope catalog only changes when the server does.
    staleTime: Infinity,
  });
}

export function useCreateToken() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ name, scopes }: { name: string; scopes: string[] | null }) =>
      tokensApi.create(name, scopes),
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
