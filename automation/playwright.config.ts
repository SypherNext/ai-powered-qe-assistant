import { defineConfig } from '@playwright/test';

// Reference configuration only. This project has no real Vespera
// Helpdesk backend to point baseURL at -- Vespera is a fictional target
// used throughout the course. These specs document the automation
// patterns the lessons teach; see automation's README for why they are
// not executed against a live server in this repo.
export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  retries: 0, // deliberately zero -- see the AI Test Maintenance lesson's
              // reply-race test for why a retry must never paper over a
              // real intermittent bug.
  reporter: 'list',
  use: {
    baseURL: process.env.VESPERA_BASE_URL || 'http://localhost:3000',
  },
});
