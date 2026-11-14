import { defineConfig } from '@playwright/test'

export default defineConfig({
  testDir: './e2e', timeout: 180000, workers: 1,
  expect: { timeout: 45000 },
  use: {
    baseURL: process.env.PHASE3_URL || 'http://127.0.0.1:5174',
    viewport: { width: 1366, height: 768 },
    actionTimeout: 15000,
    launchOptions: {
      executablePath: process.env.BROWSER_PATH || 'C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe',
    },
    screenshot: 'only-on-failure', trace: 'retain-on-failure',
  },
  reporter: [['list'], ['json', { outputFile: `../reports/${process.env.QA_REPORT_PREFIX || 'phase3'}_browser.json` }]],
})
