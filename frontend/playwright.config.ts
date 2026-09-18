import { defineConfig, devices } from "@playwright/test";

const port = Number(process.env.PLAYWRIGHT_PORT ?? 3100);
const baseURL = `http://127.0.0.1:${port}`;

export default defineConfig({
  testDir: "./tests/e2e",
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: [
    ["list"],
    ["html", { outputFolder: "playwright-report", open: "never" }],
    ["junit", { outputFile: "test-results/playwright-junit.xml" }],
  ],
  use: {
    baseURL,
    trace: "on-first-retry",
    screenshot: "only-on-failure",
    video: "retain-on-failure",
  },
  webServer: {
    command: `npm run build && cp -R .next/static .next/standalone/.next/static && cp -R public .next/standalone/public && PORT=${port} HOSTNAME=127.0.0.1 node .next/standalone/server.js`,
    url: baseURL,
    reuseExistingServer: !process.env.CI,
    timeout: 180_000,
  },
  projects: [
    {
      name: "chromium-desktop",
      grepInvert: /@mobile/,
      use: { ...devices["Desktop Chrome"] },
    },
    {
      name: "chromium-mobile",
      grep: /@mobile/,
      use: { ...devices["Pixel 7"] },
    },
  ],
});
