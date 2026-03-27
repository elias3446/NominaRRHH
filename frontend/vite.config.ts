import { defineConfig, loadEnv } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { componentTagger } from "lovable-tagger";

// https://vitejs.dev/config/
export default defineConfig(({ mode }) => {
  // Carga las variables de entorno desde la carpeta raíz (un directorio atrás: '../')
  const env = loadEnv(mode, path.resolve(__dirname, '../'), '');

  return {
    // Le enseñamos a Vite dónde está el archivo .env oficial
    envDir: "../",
    server: {
      host: "::",
      // Asignamos el puerto de Frontend dinámicamente
      port: parseInt(env.FRONTEND_PORT || "3000"),
      hmr: {
        overlay: false,
      },
    },
    plugins: [react(), mode === "development" && componentTagger()].filter(Boolean),
    resolve: {
      alias: {
        "@": path.resolve(__dirname, "./src"),
      },
      dedupe: ["react", "react-dom", "react/jsx-runtime", "react/jsx-dev-runtime"],
    },
  };
});
