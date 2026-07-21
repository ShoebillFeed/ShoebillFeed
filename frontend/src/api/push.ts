import client from "./client";

export interface VapidPublicKey {
  public_key: string;
  configured: boolean;
}

export interface PushSubscriptionCreate {
  endpoint: string;
  p256dh: string;
  auth: string;
}

export interface DryRunResult {
  count: number;
  days: number;
}

export const pushApi = {
  getVapidPublicKey: () =>
    client.get<VapidPublicKey>("/push/vapid-public-key").then((r) => r.data),

  saveSubscription: (sub: PushSubscriptionCreate) =>
    client.post("/push/subscription", sub),

  deleteSubscription: (endpoint: string) =>
    client.delete("/push/subscription", { params: { endpoint } }),

  dryRun: (days = 7) =>
    client.get<DryRunResult>("/push/dry-run", { params: { days } }).then((r) => r.data),
};
