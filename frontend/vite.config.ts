// Configuración de Vite: servidor de desarrollo en :5173 y proxy de /api hacia la API local.
import { fileURLToPath } from "node:url";
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// Carpeta seed/ del repo: api.ts la usa como datos de prueba mientras la API no responde
const seedDir = fileURLToPath(new URL("../seed", import.meta.url));

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: { "@seed": seedDir },
  },
  server: {
    port: 5173,
    // Permite servir archivos de seed/, que está fuera de frontend/
    fs: { allow: [".", seedDir] },
    // En desarrollo local la API corre en :8000 (docker compose); así no hace falta CORS
    proxy: {
      "/api": "http://localhost:8000",
    },
  },
});
