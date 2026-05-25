import { Navigate, Routes, Route } from "react-router-dom";
import AppShell from "./components/layout/AppShell";
import FeedPage from "./pages/FeedPage";
import SettingsPage from "./pages/SettingsPage";
import LoginPage from "./pages/LoginPage";
import { useMe } from "./hooks/useAuth";

function RequireAuth({ children }: { children: React.ReactNode }) {
  const { data: user, isLoading, isError } = useMe();
  if (isLoading) return null;
  if (isError || !user) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export default function App() {
  return (
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
  );
}
