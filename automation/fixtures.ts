import { test as base, type APIRequestContext } from '@playwright/test';

type SeedTicketOptions = {
  status: 'Open' | 'Waiting on Customer' | 'Resolved';
  minutesToBreach: number;
  assignedAgent?: string | null;
  priority?: 'Normal' | 'Urgent';
};

type SeededTicket = {
  id: number;
  status: string;
  priority: string;
  escalated_by_system: boolean;
  assigned_agent: string | null;
};

type TestFixtures = {
  seedTicket: (options: SeedTicketOptions) => Promise<SeededTicket>;
};

export const test = base.extend<TestFixtures>({
  // Test-scoped: hands the test a function it can call one or more
  // times to seed tickets, and tracks every ticket it creates so they
  // can all be cleaned up afterward -- regardless of how many the test
  // seeded, or whether the test passed or failed.
  seedTicket: async ({ request }, use) => {
    const createdIds: number[] = [];

    const seed = async (options: SeedTicketOptions): Promise<SeededTicket> => {
      const response = await request.post('/api/test/seed-ticket', { data: options });
      const ticket: SeededTicket = await response.json();
      createdIds.push(ticket.id);
      return ticket;
    };

    await use(seed);

    for (const id of createdIds) {
      await request.delete(`/api/test/tickets/${id}`);
    }
  },
});

export { expect } from '@playwright/test';

export async function getSlackCallsForTicket(request: APIRequestContext, ticketId: number) {
  const response = await request.get(`/api/test/slack-webhook-calls?ticketId=${ticketId}`);
  return response.json();
}
