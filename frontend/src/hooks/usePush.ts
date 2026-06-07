import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { pushApi } from "../api/push";

export function useVapidPublicKey() {
  return useQuery({
    queryKey: ["push", "vapid"],
    queryFn: pushApi.getVapidPublicKey,
  });
}

function urlBase64ToUint8Array(base64String: string): Uint8Array {
  const padding = "=".repeat((4 - (base64String.length % 4)) % 4);
  const base64 = (base64String + padding).replace(/-/g, "+").replace(/_/g, "/");
  const rawData = atob(base64);
  return Uint8Array.from([...rawData].map((c) => c.charCodeAt(0)));
}

export async function subscribeToPush(vapidPublicKey: string): Promise<PushSubscription | null> {
  if (!("serviceWorker" in navigator) || !("PushManager" in window)) return null;

  const reg = await navigator.serviceWorker.ready;
  const existing = await reg.pushManager.getSubscription();
  if (existing) return existing;

  return reg.pushManager.subscribe({
    userVisibleOnly: true,
    applicationServerKey: urlBase64ToUint8Array(vapidPublicKey),
  });
}

export async function getExistingSubscription(): Promise<PushSubscription | null> {
  if (!("serviceWorker" in navigator) || !("PushManager" in window)) return null;
  const reg = await navigator.serviceWorker.ready;
  return reg.pushManager.getSubscription();
}

export function useSavePushSubscription() {
  return useMutation({
    mutationFn: (sub: PushSubscription) => {
      const json = sub.toJSON();
      return pushApi.saveSubscription({
        endpoint: sub.endpoint,
        p256dh: (json.keys as Record<string, string>)["p256dh"],
        auth: (json.keys as Record<string, string>)["auth"],
      });
    },
  });
}

export function useDeletePushSubscription() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const sub = await getExistingSubscription();
      if (!sub) return;
      await pushApi.deleteSubscription(sub.endpoint);
      await sub.unsubscribe();
    },
    onSuccess: () => qc.invalidateQueries({ queryKey: ["push"] }),
  });
}
