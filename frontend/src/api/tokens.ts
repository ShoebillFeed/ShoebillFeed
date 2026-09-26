import client from "./client";

export interface ApiToken {
  id: string;
  name: string;
  created_at: string;
  last_used_at: string | null;
  // null means unrestricted — what every token created before scopes
  // existed carries, and what an all-boxes-ticked token is stored as.
  scopes: string[] | null;
}

export interface TokenScope {
  key: string;
  description: string;
}

export interface ApiTokenCreated extends ApiToken {
  token: string;
}

export const tokensApi = {
  list: () =>
    client.get<ApiToken[]>("/tokens").then((r) => r.data),

  create: (name: string, scopes: string[] | null) =>
    client.post<ApiTokenCreated>("/tokens", { name, scopes }).then((r) => r.data),

  scopes: () =>
    client.get<TokenScope[]>("/tokens/scopes").then((r) => r.data),

  delete: (id: string) =>
    client.delete(`/tokens/${id}`),
};
