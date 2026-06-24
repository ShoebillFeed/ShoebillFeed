import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { learningApi } from "../api/learning";

const PROFILE_KEY = ["learning", "profile"];

export function useLearningProfile() {
  return useQuery({ queryKey: PROFILE_KEY, queryFn: learningApi.profile });
}

export function useSetCategoryWeight() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, weight }: { id: string; weight: number }) =>
      learningApi.setCategoryWeight(id, weight),
    onSuccess: () => qc.invalidateQueries({ queryKey: PROFILE_KEY }),
  });
}

export function useDeleteKeyword() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (keyword: string) => learningApi.deleteKeyword(keyword),
    onSuccess: () => qc.invalidateQueries({ queryKey: PROFILE_KEY }),
  });
}
