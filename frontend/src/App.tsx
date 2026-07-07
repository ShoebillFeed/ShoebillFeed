import { useEffect } from "react";
import { Navigate, Routes, Route } from "react-router-dom";
import { isAxiosError } from "axios";
import { useTranslation } from "react-i18next";
import { useRegisterSW } from "virtual:pwa-register/react";
import AppShell from "./components/layout/AppShell";
import FeedPage from "./pages/FeedPage";
import SettingsPage from "./pages/SettingsPage";
import LoginPage from "./pages/LoginPage";
import { useMe } from "./hooks/useAuth";
import { usePreferencesStore } from "./stores/preferencesStore";
import { Toaster } from "./components/ui/Toaster";

function ThemeProvider() {
  const theme = usePreferencesStore((s) => s.theme);

  useEffect(() => {
    document.documentElement.classList.toggle("dark", theme === "dark");
  }, [theme]);

  return null;
}

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { t } = useTranslation();
  const { data: user, isLoading, isError, error, refetch, isFetching } = useMe();

  if (isLoading) {
    return (
      <div className="min-h-dvh flex items-center justify-center bg-gray-50 dark:bg-gray-950">
        <span className="text-sm text-gray-400">{t("common.loading")}</span>
      </div>
    );
  }

  if (isError) {
    // Only a real 401 means "not logged in" — anything else (timeout, network
    // error, 5xx) means the server is unreachable, not that the session is invalid.
    const status = isAxiosError(error) ? error.response?.status : undefined;
    if (status === 401) return <Navigate to="/login" replace />;

    return (
      <div className="min-h-dvh flex items-center justify-center bg-gray-50 dark:bg-gray-950 px-4">
        <div className="flex flex-col items-center gap-3 text-center">
          <p className="text-sm text-gray-500 dark:text-gray-400">{t("common.connectionError")}</p>
          <button
            onClick={() => refetch()}
            disabled={isFetching}
            className="py-2 px-4 text-sm font-medium rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 transition-colors"
          >
            {t("common.retry")}
          </button>
        </div>
      </div>
    );
  }

  if (!user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

function UpdateBanner() {
  const { t } = useTranslation();
  const { needRefresh: [needRefresh], updateServiceWorker } = useRegisterSW();

  if (!needRefresh) return null;

  return (
    <div className="fixed bottom-0 left-0 right-0 z-50 flex items-center justify-between gap-3 px-4 py-3 bg-indigo-600 text-white text-sm shadow-lg">
      <span>{t("pwa.updateAvailable")}</span>
      <button
        onClick={() => updateServiceWorker(true)}
        className="px-3 py-1 rounded bg-white text-indigo-600 font-medium hover:bg-indigo-50 transition-colors"
      >
        {t("pwa.reload")}
      </button>
    </div>
  );
}

export default function App() {
  return (
    <Toaster>
      <ThemeProvider />
      <UpdateBanner />
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/*"
          element={
            <RequireAuth>
              <AppShell>
                <Routes>
                  <Route path="/" element={<FeedPage />} />
                  <Route path="/settings" element={<SettingsPage />} />
                </Routes>
              </AppShell>
            </RequireAuth>
          }
        />
      </Routes>
    </Toaster>
  );
}
