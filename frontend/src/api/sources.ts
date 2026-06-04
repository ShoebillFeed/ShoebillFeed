import client from "./client";
import type { Source, SourceCreate, SourceUpdate } from "../types/source";

export const sourcesApi = {
  list: () => client.get<Source[]>("/sources").then((r) => r.data),
  listShared: () => client.get<Source[]>("/sources/shared").then((r) => r.data),
  create: (data: SourceCreate) => client.post<Source>("/sources", data).then((r) => r.data),
  update: (id: string, data: SourceUpdate) =>
    client.patch<Source>(`/sources/${id}`, data).then((r) => r.data),
  delete: (id: string) => client.delete(`/sources/${id}`),
  fetch: (id: string) => client.post(`/sources/${id}/fetch`).then((r) => r.data),
  fetchAll: () => client.post("/sources/fetch-all").then((r) => r.data),
  export: () => client.get<SourceCreate[]>("/sources/export").then((r) => r.data),
  import: (data: SourceCreate[]) => client.post<Source[]>("/sources/import", data).then((r) => r.data),
};
