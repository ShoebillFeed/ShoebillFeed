import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { settingsApi, type UserSettingsUpdate } from "../api/settings";

export function useAdvancedSettings() {
  return useQuery({
    queryKey: ["settings", "advanced"],
    queryFn: settingsApi.getAdvanced,
  });
}

export function useUpdateAdvancedSettings() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (data: UserSettingsUpdate) => settingsApi.updateAdvanced(data),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["settings", "advanced"] }),
  });
}
