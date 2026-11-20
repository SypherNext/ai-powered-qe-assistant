import { test, expect, getSlackCallsForTicket } from '../fixtures';

// SLA breach on an eligible ticket escalates correctly -- the first
// scenario from the AI Test Generation lesson's approved set, automated
// per the AI Automation Generation lesson's QE-corrected version.
test('SLA breach on an eligible ticket escalates correctly', async ({ seedTicket, page, request }) => {
  const ticket = await seedTicket({
    status: 'Open',
    minutesToBreach: 61,
    assignedAgent: 'agent-priya', // fake test-fixture identifier, not a real Vespera user
  });

  await page.goto(`/dashboard/tickets/${ticket.id}`);

  // Escalation is processed by an async background job, not the page
  // load -- this waits, with Playwright's built-in retry, for the badge
  // to actually say "Urgent" instead of assuming it already does.
  await expect(page.getByTestId('priority-pill')).toHaveText('Urgent');

  // The Slack call is fired by the backend job too, so it can lag
  // slightly behind the badge update -- poll the capture endpoint
  // instead of assuming both land at the same moment.
  await expect
    .poll(async () => (await getSlackCallsForTicket(request, ticket.id)).length, {
      message: 'waiting for the escalation webhook to fire',
      timeout: 15_000,
    })
    .toBe(1);

  const [webhookCall] = await getSlackCallsForTicket(request, ticket.id);
  expect(webhookCall.channel).toBe('team-agent-priya');
  expect(webhookCall.text).toContain('escalated');
});
