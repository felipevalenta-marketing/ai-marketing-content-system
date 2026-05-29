import { createServer } from "vite";
import react from "@vitejs/plugin-react";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const frontendRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");

const server = await createServer({
  configFile: false,
  root: frontendRoot,
  plugins: [react()],
  server: {
    host: "127.0.0.1",
    port: 5173,
    strictPort: true,
    proxy: {
      "/health": "http://127.0.0.1:8000",
      "/config": "http://127.0.0.1:8000",
      "/generate": "http://127.0.0.1:8000",
      "/workflow": "http://127.0.0.1:8000",
      "/campaign": "http://127.0.0.1:8000",
      "/assets": "http://127.0.0.1:8000",
      "/reports": "http://127.0.0.1:8000",
      "/storage": "http://127.0.0.1:8000",
      "/analytics": "http://127.0.0.1:8000",
      "/brands": "http://127.0.0.1:8000",
    },
  },
});

await server.listen();
server.printUrls();
