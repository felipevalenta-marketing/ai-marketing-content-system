import { preview } from "vite";
import { fileURLToPath } from "node:url";
import { dirname, resolve } from "node:path";

const frontendRoot = resolve(dirname(fileURLToPath(import.meta.url)), "..");

const server = await preview({
  configFile: false,
  root: frontendRoot,
  preview: {
    host: "127.0.0.1",
    port: 4173,
    strictPort: true,
  },
});

server.printUrls();
