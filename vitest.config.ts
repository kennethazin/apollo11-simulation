import { defineConfig } from "vitest/config";

export default defineConfig({
  test: {
    include: ["**/*.test.tsx"],
    globals: true,
    environment: "jsdom",
  },
});
