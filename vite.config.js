/// <reference types="vitest" />

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import cesium from "vite-plugin-cesium"; // Import the plugin
import tailwindcss from "@tailwindcss/vite";

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react(), cesium(), tailwindcss()],
  test: {
    environment: "jsdom", // Or 'happy-dom'
    globals: true,
  },
});
