import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  resolve: {
    tsconfigPaths: true,
  },
  test: {
    environment: "jsdom",
    setupFiles: ["./tests/setup.ts"],
    include: ["tests/unit/**/*.test.{ts,tsx}"],
    coverage: {
      provider: "v8",
      reporter: ["text", "json-summary", "lcov", "html"],
      reportsDirectory: "coverage",
      include: [
        "lib/textValidation.ts",
        "components/AssessmentReview.tsx",
        "components/DocumentUploadScreen.tsx",
        "components/LikertScreen.tsx",
        "components/PillSelectQuestion.tsx",
        "components/TextQuestion.tsx",
      ],
      thresholds: {
        lines: 60,
        statements: 60,
        functions: 60,
        branches: 50,
      },
    },
  },
});
