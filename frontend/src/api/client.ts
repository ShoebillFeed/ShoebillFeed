import axios from "axios";

const client = axios.create({
  baseURL: "/api",
  headers: { "Content-Type": "application/json" },
  withCredentials: true,
  paramsSerializer: {
    serialize: (params: Record<string, unknown>) => {
      const parts: string[] = [];
      for (const [key, value] of Object.entries(params)) {
        if (value === undefined || value === null) continue;
        if (Array.isArray(value)) {
          for (const v of value) parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(String(v))}`);
        } else {
          parts.push(`${encodeURIComponent(key)}=${encodeURIComponent(String(value))}`);
        }
      }
      return parts.join("&");
    },
  },
});

client.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error.response?.status === 401) {
      const url = error.config?.url ?? "";
      // Don't redirect if the failing call is /auth/me itself (handled by RequireAuth)
      if (!url.includes("/auth/")) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(error);
  }
);

export default client;
