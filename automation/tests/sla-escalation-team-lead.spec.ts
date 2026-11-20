import { test, expect, getSlackCallsForTicket } from '../fixtures';

// "Ticket with no assigned agent escalates to the team lead" -- the
// QE-corrected version from the AI Automation Generation lesson's
// exercise. Fixed three planted issues from the AI-generated draft:
// poor isolation (discarded the seed response instead of capturing the
// ticket id), a brittle positional XPath selector, and a disguised
// non-determinism pattern (a reload-and-sleep loop standing in for a
// real retrying assertion).
test('unassigned ticket escalates and notifies the team lead', async ({ seedTicket, page, request }) => {
  const ticket = await seedTicket({
    status: 'Open',
    minutesToBreach: 61,
    assignedAgent: null,
  });

  await page.goto(`/dashboard/tickets/${ticket.id}`);

  await expect(page.getByTestId('priority-pill')).toHaveText('Urgent');

  await expect
    .poll(async () => (await getSlackCallsForTicket(request, ticket.id)).length, {
      message: 'waiting for the escalation webhook to fire',
      timeout: 15_000,
    })
    .toBe(1);

  const [webhookCall] = await getSlackCallsForTicket(request, ticket.id);
  expect(webhookCall.channel).toBe('team-lead');
});
