import { useState } from "react";
import type { ReactNode } from "react";
import { Plus, Trash2, ShieldCheck, KeyRound, BookOpen, Star, Bookmark, Newspaper, Radio, Tag, Clock } from "lucide-react";
import { useTranslation } from "react-i18next";
import { useUsers, useCreateUser, useDeleteUser, useResetUserPassword, useUserStats } from "../../hooks/useAuth";
import type { UserStats } from "../../api/auth";

export default function UsersPanel() {
  const { t } = useTranslation();
  const { data: users, isLoading } = useUsers();
  const { data: statsData } = useUserStats();
  const createUser = useCreateUser();
  const deleteUser = useDeleteUser();
  const resetPassword = useResetUserPassword();

  const statsMap = new Map<string, UserStats>(statsData?.map((s) => [s.user_id, s]) ?? []);

  const [showForm, setShowForm] = useState(false);
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [isAdmin, setIsAdmin] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const [resetUserId, setResetUserId] = useState<string | null>(null);
  const [resetPassword1, setResetPassword1] = useState("");
  const [resetError, setResetError] = useState<string | null>(null);
  const [resetSuccess, setResetSuccess] = useState<string | null>(null);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    setFormError(null);
    try {
      await createUser.mutateAsync({ username, password, is_admin: isAdmin });
      setUsername("");
      setPassword("");
      setIsAdmin(false);
      setShowForm(false);
    } catch (err: any) {
      setFormError(err?.response?.data?.detail ?? t("users.failedToCreate"));
    }
  };

  const openReset = (id: string) => {
    setResetUserId(id);
    setResetPassword1("");
    setResetError(null);
    setResetSuccess(null);
  };

  const handleReset = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!resetUserId) return;
    setResetError(null);
    setResetSuccess(null);
    try {
      await resetPassword.mutateAsync({ id: resetUserId, password: resetPassword1 });
      setResetSuccess(t("users.resetSuccess"));
      setResetPassword1("");
      setTimeout(() => { setResetUserId(null); setResetSuccess(null); }, 1500);
    } catch (err: any) {
      setResetError(err?.response?.data?.detail ?? t("users.resetFailed"));
    }
  };

  return (
    <div>
      <div className="flex items-center justify-between mb-4">
        <h2 className="font-semibold text-gray-900 dark:text-gray-100">{t("users.title")}</h2>
        <button
          onClick={() => { setShowForm(true); setFormError(null); }}
          className="flex items-center gap-1.5 px-3 py-1.5 text-sm bg-indigo-600 text-white rounded hover:bg-indigo-700 transition-colors"
        >
          <Plus size={14} /> {t("users.addUser")}
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={handleCreate}
          className="mb-4 p-4 border border-gray-200 dark:border-gray-700 rounded-lg bg-gray-50 dark:bg-gray-800/50 flex flex-col gap-3"
        >
          <h3 className="font-medium text-sm">{t("users.newUser")}</h3>
          <div>
            <label className="block text-sm font-medium mb-1">{t("users.username")}</label>
            <input
              className={inputClass}
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              minLength={2}
              placeholder="username"
            />
          </div>
          <div>
            <label className="block text-sm font-medium mb-1">{t("users.password")}</label>
            <input
              type="password"
              className={inputClass}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              minLength={6}
              placeholder={t("users.passwordPlaceholder")}
            />
          </div>
          <label className="flex items-center gap-2 text-sm cursor-pointer">
            <input
              type="checkbox"
              checked={isAdmin}
              onChange={(e) => setIsAdmin(e.target.checked)}
              className="rounded"
            />
            {t("users.admin")}
          </label>
          {formError && <p className="text-sm text-red-500">{formError}</p>}
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => setShowForm(false)}
              className="flex-1 px-4 py-2 text-sm font-medium rounded bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 transition-colors"
            >
              {t("common.cancel")}
            </button>
            <button
              type="submit"
              disabled={createUser.isPending}
              className="flex-1 px-4 py-2 text-sm font-medium rounded bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 transition-colors"
            >
              {createUser.isPending ? t("users.creating") : t("common.create")}
            </button>
          </div>
        </form>
      )}

      {isLoading && <p className="text-sm text-gray-400">{t("common.loading")}</p>}

      <div className="flex flex-col gap-2">
        {users?.map((u) => {
          const s = statsMap.get(u.id);
          return (
          <div key={u.id}>
            <div className="p-3 bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg">
              <div className="flex items-center gap-3">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-1.5">
                    <span className="text-sm font-medium">{u.username}</span>
                    {u.is_admin && (
                      <span className="inline-flex items-center gap-0.5 text-xs text-indigo-600 dark:text-indigo-400">
                        <ShieldCheck size={12} /> admin
                      </span>
                    )}
                  </div>
                </div>
                <button
                  title={t("users.resetPassword")}
                  onClick={() => resetUserId === u.id ? setResetUserId(null) : openReset(u.id)}
                  className="p-1.5 rounded text-gray-400 hover:text-indigo-500 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                >
                  <KeyRound size={14} />
                </button>
                <button
                  title={t("users.deleteUser")}
                  onClick={() => {
                    if (confirm(t("users.deleteConfirm", { name: u.username })))
                      deleteUser.mutate(u.id);
                  }}
                  className="p-1.5 rounded text-gray-400 hover:text-red-500 hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                >
                  <Trash2 size={14} />
                </button>
              </div>

              {s && <UserStatsRow stats={s} />}
            </div>

            {resetUserId === u.id && (
              <form
                onSubmit={handleReset}
                className="mt-1 p-3 border border-indigo-200 dark:border-indigo-800 rounded-lg bg-indigo-50/50 dark:bg-indigo-950/30 flex flex-col gap-2"
              >
                <p className="text-xs font-medium text-gray-600 dark:text-gray-400">
                  {t("users.resetPassword")} — {u.username}
                </p>
                <input
                  type="password"
                  className={inputClass}
                  value={resetPassword1}
                  onChange={(e) => setResetPassword1(e.target.value)}
                  required
                  minLength={6}
                  placeholder={t("users.passwordPlaceholder")}
                  autoFocus
                />
                {resetError && <p className="text-xs text-red-500">{resetError}</p>}
                {resetSuccess && <p className="text-xs text-green-600 dark:text-green-400">{resetSuccess}</p>}
                <div className="flex gap-2">
                  <button
                    type="button"
                    onClick={() => setResetUserId(null)}
                    className="flex-1 px-3 py-1.5 text-xs font-medium rounded bg-gray-100 text-gray-700 hover:bg-gray-200 dark:bg-gray-700 dark:text-gray-300 transition-colors"
                  >
                    {t("common.cancel")}
                  </button>
                  <button
                    type="submit"
                    disabled={resetPassword.isPending}
                    className="flex-1 px-3 py-1.5 text-xs font-medium rounded bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 transition-colors"
                  >
                    {resetPassword.isPending ? "…" : t("users.resetPassword")}
                  </button>
                </div>
              </form>
            )}
          </div>
          );
        })}
      </div>
    </div>
  );
}

const inputClass =
  "w-full px-3 py-2 text-sm rounded border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500";

function UserStatsRow({ stats: s }: { stats: UserStats }) {
  const lastActive = s.last_active ? formatRelative(s.last_active) : null;
  return (
    <div className="mt-2.5 pt-2.5 border-t border-gray-100 dark:border-gray-800 flex flex-wrap gap-x-4 gap-y-1">
      <StatChip icon={<Newspaper size={11} />} label={`${s.total_items.toLocaleString()} fetched`} />
      <StatChip icon={<BookOpen size={11} />} label={`${s.read_count.toLocaleString()} read`} />
      <StatChip icon={<Star size={11} />} label={`${s.starred_count.toLocaleString()} starred`} />
      <StatChip icon={<Bookmark size={11} />} label={`${s.read_later_count.toLocaleString()} saved`} />
      <StatChip icon={<Radio size={11} className="opacity-50" />} label={`${s.sources_count} sources`} />
      <StatChip icon={<Tag size={11} />} label={`${s.categories_count} categories`} />
      {lastActive && <StatChip icon={<Clock size={11} />} label={lastActive} />}
    </div>
  );
}

function StatChip({ icon, label }: { icon: ReactNode; label: string }) {
  return (
    <span className="inline-flex items-center gap-1 text-xs text-gray-400 dark:text-gray-500">
      {icon} {label}
    </span>
  );
}

function formatRelative(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 60) return `active ${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `active ${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 30) return `active ${days}d ago`;
  return `active ${Math.floor(days / 30)}mo ago`;
}
