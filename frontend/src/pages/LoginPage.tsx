import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { ShoebillIcon } from "../components/icons/ShoebillIcon";
import { useLogin, useMe } from "../hooks/useAuth";

export default function LoginPage() {
  const navigate = useNavigate();
  const { data: user } = useMe();
  const login = useLogin();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  useEffect(() => {
    if (user) navigate("/", { replace: true });
  }, [user, navigate]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await login.mutateAsync({ username, password });
      navigate("/", { replace: true });
    } catch {
      // error shown via login.error
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 dark:bg-gray-950 px-4">
      <div className="w-full max-w-sm">
        <div className="flex flex-col items-center mb-8">
          <div className="flex items-center gap-2 text-indigo-600 dark:text-indigo-400 mb-2">
            <ShoebillIcon size={28} />
            <span className="text-2xl font-bold">Shoebill Feed</span>
          </div>
          <p className="text-sm text-gray-500 dark:text-gray-400">Sign in to your account</p>
        </div>

        <form
          onSubmit={handleSubmit}
          className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-700 p-6 flex flex-col gap-4 shadow-sm"
        >
          <div>
            <label className="block text-sm font-medium mb-1.5">Username</label>
            <input
              type="text"
              autoComplete="username"
              required
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className={inputClass}
            />
          </div>

          <div>
            <label className="block text-sm font-medium mb-1.5">Password</label>
            <input
              type="password"
              autoComplete="current-password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={inputClass}
            />
          </div>

          {login.error && (
            <p className="text-sm text-red-500">
              Invalid username or password.
            </p>
          )}

          <button
            type="submit"
            disabled={login.isPending}
            className="w-full py-2 px-4 text-sm font-medium rounded-lg bg-indigo-600 text-white hover:bg-indigo-700 disabled:opacity-50 transition-colors"
          >
            {login.isPending ? "Signing in…" : "Sign in"}
          </button>
        </form>
      </div>
    </div>
  );
}

const inputClass =
  "w-full px-3 py-2 text-sm rounded-lg border border-gray-300 dark:border-gray-600 bg-white dark:bg-gray-800 focus:outline-none focus:ring-2 focus:ring-indigo-500";
