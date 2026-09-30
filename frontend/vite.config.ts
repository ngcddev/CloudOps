// Configuración de Vite: servidor de desarrollo en :5173 y proxy de /api hacia la API local.
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    // En desarrollo local la API corre en :8000 (docker compose); así no hace falta CORS
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
