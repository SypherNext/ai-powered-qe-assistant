// Example of what the scanner flags -- do not commit real code like this.
import { test, expect } from '@playwright/test';

test('escalation webhook fires with auth header', async ({ request }) => {
  const response = await request.post('/api/webhooks/slack', {
    headers: {
      Authorization: 'Bearer sk-fake-1234567890abcdef', // flagged: sk- style key literal
    },
    data: { ticketId: 4821 },
  });
  expect(response.ok()).toBeTruthy();
});
