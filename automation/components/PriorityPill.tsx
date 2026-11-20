// The redesigned priority badge from the "AI Test Maintenance" lesson.
// The original <span data-testid="ticket-priority-badge"> badge became
// this component -- same information, same visual result, completely
// different markup. The one attribute that exists purely so tests can
// find it (data-testid) has to be carried over deliberately; nothing
// about a component redesign preserves it automatically.

export type PriorityLevel = 'Normal' | 'Urgent';

export function PriorityPill({ level }: { level: PriorityLevel }) {
  return (
    <div
      className={`priority-pill priority-pill--${level.toLowerCase()}`}
      data-testid="priority-pill"
    >
      <span className="priority-pill__label">{level}</span>
    </div>
  );
}
