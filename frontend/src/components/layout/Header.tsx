import type { ReactNode } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { Newspaper, Settings, LogOut, Sun, Moon } from "lucide-react";
import { ShoebillIcon } from "../icons/ShoebillIcon";
import { cn } from "../../lib/utils";
import { useMe, useLogout } from "../../hooks/useAuth";
import { usePreferencesStore } from "../../stores/preferencesStore";

function ThemeToggle() {
  const theme = usePreferencesStore((s) => s.theme);
  const setTheme = usePreferencesStore((s) => s.setTheme);

  return (
    <button
      onClick={() => setTheme(theme === "dark" ? "light" : "dark")}
      title={`Switch to ${theme === "dark" ? "light" : "dark"} mode`}
      className="flex items-center gap-1.5 px-2 py-1.5 rounded-md text-sm text-gray-500 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-gray-100 dark:hover:bg-gray-800 transition-colors"
    >
      {theme === "dark" ? <Sun size={16} /> : <Moon size={16} />}
    </button>
  );
}

export default function Header() {
  const { pathname } = useLocation();
  const navigate = useNavigate();
  const { data: user } = useMe();
  const logout = useLogout();

  const handleLogout = async () => {
    await logout.mutateAsync();
    navigate("/login", { replace: true });
  };

  return (
    <header className="sticky top-0 z-50 bg-white dark:bg-gray-900 border-b border-gray-200 dark:border-gray-800 shadow-sm">
      <div className="container mx-auto px-4 max-w-5xl h-14 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2 font-bold text-lg text-indigo-600 dark:text-indigo-400">
          <ShoebillIcon size={20} />
          <span className="hidden sm:inline">Shoebill Feed</span>
          <span className="sm:hidden">SF</span>
        </Link>

        <nav className="flex items-center gap-1">
          <NavLink to="/" active={pathname === "/"} icon={<Newspaper size={16} />} label="Feed" />
          <NavLink to="/settings" active={pathname === "/settings"} icon={<Settings size={16} />} label="Settings" />

          <ThemeToggle />

          {user && (
            <div className="flex items-center gap-2 ml-2 pl-2 border-l border-gray-200 dark:border-gray-700">
              <span className="hidden sm:inline text-xs text-gray-500 dark:text-gray-400">
                {user.username}
              </span>
              <button
                onClick={handleLogout}
                title="Sign out"
                className="flex items-center gap-1.5 px-2 py-1.5 rounded-md text-sm text-gray-500 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-gray-100 dark:hover:bg-gray-800 transition-colors"
              >
                <LogOut size={16} />
                <span className="hidden sm:inline">Sign out</span>
              </button>
            </div>
          )}
        </nav>
      </div>
    </header>
  );
}

function NavLink({ to, active, icon, label }: { to: string; active: boolean; icon: ReactNode; label: string }) {
  return (
    <Link
      to={to}
      className={cn(
        "flex items-center gap-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors",
        active
          ? "bg-indigo-50 text-indigo-700 dark:bg-indigo-950 dark:text-indigo-300"
          : "text-gray-600 hover:text-gray-900 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-gray-100 dark:hover:bg-gray-800"
      )}
    >
      {icon}
      <span className="hidden sm:inline">{label}</span>
    </Link>
  );
}
