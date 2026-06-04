/// <reference types="vitest/config" />
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      // Dev convenience: proxy API calls to the FastAPI backend.
      // Port 8077 (8000 is commonly occupied by other local apps).
      "/api": "http://localhost:8077",
    },
  },
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./src/test-setup.ts"],
  },
});
