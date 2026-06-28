import client from "./client";

export interface ApiToken {
  id: string;
  name: string;
  created_at: string;
  last_used_at: string | null;
}

export interface ApiTokenCreated extends ApiToken {
  token: string;
}

export const tokensApi = {
  list: () =>
    client.get<ApiToken[]>("/tokens").then((r) => r.data),

  create: (name: string) =>
    client.post<ApiTokenCreated>("/tokens", { name }).then((r) => r.data),

  delete: (id: string) =>
    client.delete(`/tokens/${id}`),
};
