import client from "./client";

export interface AuthUser {
  id: string;
  username: string;
  is_admin: boolean;
}

export const authApi = {
  login: (username: string, password: string) =>
    client.post<AuthUser>("/auth/login", { username, password }).then((r) => r.data),
  logout: () => client.post("/auth/logout"),
  me: () => client.get<AuthUser>("/auth/me").then((r) => r.data),
  listUsers: () => client.get<AuthUser[]>("/auth/users").then((r) => r.data),
  createUser: (username: string, password: string, is_admin: boolean) =>
    client.post<AuthUser>("/auth/users", { username, password, is_admin }).then((r) => r.data),
  deleteUser: (id: string) => client.delete(`/auth/users/${id}`),
};
