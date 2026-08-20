import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { VitePWA } from "vite-plugin-pwa";

// No @types/node in this project -- this file is the only place needing
// process.env, so a minimal local ambient declaration beats adding a
// dependency for one line.
declare const process: { env: Record<string, string | undefined> };

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
    VitePWA({
      registerType: "prompt",
      includeAssets: ["icon-192.png", "icon-512.png", "apple-touch-icon.png"],
      manifest: {
        name: "Shoebill Feed",
        short_name: "Shoebill",
        description: "Self-hosted news aggregator with LLM-powered categorization",
        theme_color: "#4f46e5",
        background_color: "#000000",
        display: "standalone",
        start_url: "/",
        icons: [
          {
            src: "/icon-192.png",
            sizes: "192x192",
            type: "image/png",
          },
          {
            src: "/icon-512.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "any",
          },
          {
            src: "/icon-512.png",
            sizes: "512x512",
            type: "image/png",
            purpose: "maskable",
          },
        ],
      },
      workbox: {
        importScripts: ["/push-sw.js"],
        // Default 2 MiB precache cap -- the main bundle eagerly imports all
        // 20+ i18n locale files (no per-language code-splitting), so fully
        // populating every language's translations pushed it past that.
        // Raised with headroom rather than tuned to the exact current size,
        // so routine future key additions don't re-trip this.
        maximumFileSizeToCacheInBytes: 4 * 1024 * 1024,
        runtimeCaching: [
          {
            // Auth state must always reflect the live session/cookie — never serve
            // a stale cached /auth/me or /auth/login response.
            urlPattern: /^\/api\/auth\//,
            handler: "NetworkOnly",
          },
          {
            // Cache API responses with NetworkFirst — serve stale feed if offline
            urlPattern: /^\/api\//,
            handler: "NetworkFirst",
            options: {
              cacheName: "api-cache",
              expiration: { maxEntries: 200, maxAgeSeconds: 60 * 60 * 24 },
              networkTimeoutSeconds: 5,
            },
          },
        ],
      },
    }),
  ],
  server: {
    // Vite 6 rejects requests whose Host header isn't localhost/127.0.0.1 by
    // default (DNS-rebinding protection) -- fatal behind a reverse proxy
    // terminating a real domain. Opt in per-deployment via env var rather
    // than hardcoding a domain here, since this file is shared by everyone
    // running the dev stack.
    allowedHosts: process.env.VITE_ALLOWED_HOSTS
      ? process.env.VITE_ALLOWED_HOSTS.split(",").map((h: string) => h.trim())
      : undefined,
    proxy: {
      "/api": {
        target: "http://backend:8000",
        changeOrigin: true,
      },
    },
  },
});
