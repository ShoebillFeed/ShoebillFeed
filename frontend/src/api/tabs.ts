import client from "./client";
import type { UserTab, UserTabCreate, UserTabUpdate } from "../types/tabs";

export const tabsApi = {
  list: () => client.get<UserTab[]>("/tabs").then((r) => r.data),
  create: (data: UserTabCreate) => client.post<UserTab>("/tabs", data).then((r) => r.data),
  update: (id: string, data: UserTabUpdate) =>
    client.patch<UserTab>(`/tabs/${id}`, data).then((r) => r.data),
  delete: (id: string) => client.delete(`/tabs/${id}`),
};
