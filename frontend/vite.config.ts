import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    proxy: {
      "/health": "http://127.0.0.1:8000",
      "/config": "http://127.0.0.1:8000",
      "/generate": "http://127.0.0.1:8000",
      "/workflow": "http://127.0.0.1:8000",
      "/campaign": "http://127.0.0.1:8000",
      "/assets": "http://127.0.0.1:8000",
      "/reports": "http://127.0.0.1:8000",
      "/storage": "http://127.0.0.1:8000",
      "/observability": "http://127.0.0.1:8000",
    },
  },
});
