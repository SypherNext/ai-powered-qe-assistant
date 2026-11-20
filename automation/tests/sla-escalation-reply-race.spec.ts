import { test, expect } from '../fixtures';

// Real race condition from the "AI Test Maintenance" lesson: Vespera's
// SLA-check cron job and its "agent replied" webhook handler can race.
// The correct fix lives in the reply handler (cancel an escalation only
// when it's still pending, never when it's already active) -- NOT in
// this test. An AI-proposed fix that adds `test.describe.configure({
// retries: 3 })` here would make the test green while leaving the real
// bug fully live; that fix is deliberately not applied anywhere in this
// repo. This test stays exactly as strict as it was written.
test('an agent reply arriving after escalation has already fired must not cancel it', async ({
  seedTicket,
  page,
  request,
}) => {
  const ticket = await seedTicket({
    status: 'Open',
    minutesToBreach: 61,
    assignedAgent: 'agent-priya', // fake test-fixture identifier, not a real Vespera user
  });

  // Trigger the SLA-check cron job directly instead of waiting for its
  // real interval -- this is what actually commits the escalation.
  await request.post('/api/test/trigger-sla-check');

  await expect(page.getByTestId('priority-pill')).toHaveText('Urgent');

  // The escalation has already fired at this point. A reply landing
  // now should have no effect on it -- only a *pending* escalation, one
  // that hasn't fired yet, should ever be cancelled by a reply.
  await request.post('/api/test/simulate-agent-reply', {
    data: { ticketId: ticket.id, agent: 'agent-priya' },
  });

  await page.reload();
  await expect(page.getByTestId('priority-pill')).toHaveText('Urgent');

  const ticketState = await (await request.get(`/api/test/tickets/${ticket.id}`)).json();
  expect(ticketState.escalated_by_system).toBe(true);
});
