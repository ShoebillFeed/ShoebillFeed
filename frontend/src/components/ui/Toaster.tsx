import { createContext, useContext, useState, useCallback } from "react";
import * as T from "@radix-ui/react-toast";
import { X } from "lucide-react";
import { cn } from "../../lib/utils";

type ToastType = "success" | "error" | "info" | "confirm";

type ToastItem = {
  id: string;
  message: string;
  type: ToastType;
  onConfirm?: () => void;
  confirmLabel?: string;
};

type ToastAPI = {
  success: (msg: string) => void;
  error: (msg: string) => void;
  confirm: (msg: string, onConfirm: () => void, confirmLabel?: string) => void;
};

const ToastCtx = createContext<ToastAPI>({
  success: () => {},
  error: () => {},
  confirm: () => {},
});

export function useToast() {
  return useContext(ToastCtx);
}

export function Toaster({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastItem[]>([]);

  const remove = useCallback((id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  }, []);

  const add = useCallback((item: Omit<ToastItem, "id">) => {
    const id = Math.random().toString(36).slice(2);
    setToasts((prev) => [...prev, { id, ...item }]);
  }, []);

  const api: ToastAPI = {
    success: (msg) => add({ message: msg, type: "success" }),
    error: (msg) => add({ message: msg, type: "error" }),
    confirm: (msg, onConfirm, confirmLabel = "Delete") =>
      add({ message: msg, type: "confirm", onConfirm, confirmLabel }),
  };

  return (
    <ToastCtx.Provider value={api}>
      <T.Provider swipeDirection="right">
        {children}
        {toasts.map((t) => (
          <T.Root
            key={t.id}
            defaultOpen
            onOpenChange={(open) => { if (!open) remove(t.id); }}
            duration={t.type === "confirm" ? 8000 : 3500}
            className={cn(
              "flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg border text-sm",
              "data-[state=open]:animate-in data-[state=closed]:animate-out",
              "data-[state=closed]:slide-out-to-right-full data-[state=open]:slide-in-from-right-full",
              "transition-all duration-200",
              t.type === "success" && "bg-green-50 dark:bg-green-900/40 border-green-200 dark:border-green-800 text-green-800 dark:text-green-200",
              t.type === "error" && "bg-red-50 dark:bg-red-900/40 border-red-200 dark:border-red-800 text-red-800 dark:text-red-200",
              (t.type === "info" || t.type === "confirm") && "bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700 text-gray-800 dark:text-gray-200",
            )}
          >
            <T.Description className="flex-1 leading-snug">{t.message}</T.Description>
            {t.type === "confirm" && t.onConfirm && (
              <T.Action altText={t.confirmLabel ?? "Delete"} asChild>
                <button
                  onClick={() => { t.onConfirm!(); remove(t.id); }}
                  className="shrink-0 px-2.5 py-1 rounded text-xs font-medium bg-red-600 text-white hover:bg-red-700 transition-colors"
                >
                  {t.confirmLabel ?? "Delete"}
                </button>
              </T.Action>
            )}
            <T.Close asChild>
              <button className="shrink-0 text-current opacity-40 hover:opacity-70 transition-opacity">
                <X size={14} />
              </button>
            </T.Close>
          </T.Root>
        ))}
        <T.Viewport className="fixed bottom-4 right-4 flex flex-col gap-2 w-80 max-w-[calc(100vw-2rem)] z-50 outline-none" />
      </T.Provider>
    </ToastCtx.Provider>
  );
}
