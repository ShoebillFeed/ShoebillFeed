import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { authApi } from "../api/auth";

export function useUsers() {
  return useQuery({ queryKey: ["auth", "users"], queryFn: authApi.listUsers });
}

export function useCreateUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ username, password, is_admin }: { username: string; password: string; is_admin: boolean }) =>
      authApi.createUser(username, password, is_admin),
    onSuccess: () => qc.invalidateQueries({ queryKey: ["auth", "users"] }),
  });
}

export function useDeleteUser() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: authApi.deleteUser,
    onSuccess: () => qc.invalidateQueries({ queryKey: ["auth", "users"] }),
  });
}

export function useMe() {
  return useQuery({
    queryKey: ["auth", "me"],
    queryFn: authApi.me,
    retry: false,
    staleTime: 5 * 60 * 1000,
  });
}

export function useLogin() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ username, password }: { username: string; password: string }) =>
      authApi.login(username, password),
    onSuccess: (user) => {
      qc.setQueryData(["auth", "me"], user);
    },
  });
}

export function useLogout() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: authApi.logout,
    onSuccess: () => {
      qc.clear();
    },
  });
}
