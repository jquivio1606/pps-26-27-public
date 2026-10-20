import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// El build se genera en `frontend/dist` y FastAPI lo sirve como archivos
// estáticos (ver backend/app/main.py). En desarrollo, el servidor de Vite
// hace de proxy hacia la API para evitar problemas de CORS.
const API_TARGET = process.env.CINE_API_TARGET || "http://127.0.0.1:8000";
const proxyPaths = ["/auth", "/movies", "/showtimes", "/tickets", "/api", "/health", "/docs", "/redoc", "/openapi.json"];

export default defineConfig({
  plugins: [react()],
  base: "/",
  build: {
    outDir: "dist",
    emptyOutDir: true,
  },
  server: {
    port: 5173,
    proxy: Object.fromEntries(proxyPaths.map((p) => [p, { target: API_TARGET, changeOrigin: true }])),
  },
  preview: {
    port: 4173,
  },
});
