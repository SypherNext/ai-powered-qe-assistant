"""TestReviewer -- deterministic code, never an LLM call. Applies the
weak-test-pattern checklist from the AI Test Generation lesson to
AI-generated scenarios. No LLMProvider import anywhere in this file --
that absence is structural, not incidental, and is asserted by a test."""

from __future__ import annotations

from .models import ReviewResult, TestScenario


class ChecklistTestReviewer:
    """Simplified -- real language understanding would catch more than
    these heuristics do -- but the simplification is in the heuristics'
    sophistication, never in whether this class calls a model. It
    doesn't, and can't."""

    VAGUE_MARKERS = ("works", "updates", "behaves as expected", "looks correct", "handled correctly")

    def __init__(self, required_edge_cases: list[str]) -> None:
        self._required_edge_cases = required_edge_cases

    def review(self, scenarios: list[TestScenario]) -> ReviewResult:
        approved: list[TestScenario] = []
        rejected: list[tuple[TestScenario, str]] = []
        seen_setups: set[str] = set()

        for scenario in scenarios:
            outcome = scenario.expected_outcome.lower()
            names_something_specific = any(ch.isdigit() or ch in "\"'" for ch in scenario.expected_outcome)

            if any(marker in outcome for marker in self.VAGUE_MARKERS) and not names_something_specific:
                rejected.append((scenario, "weak assertion -- outcome doesn't name a specific field or value"))
                continue

            normalized_setup = " ".join(scenario.setup.lower().split())
            if normalized_setup in seen_setups:
                rejected.append((scenario, "duplicate -- same setup as an already-approved scenario"))
                continue

            seen_setups.add(normalized_setup)
            approved.append(scenario)

        covered_text = " ".join(f"{s.setup} {s.expected_outcome}".lower() for s in approved)
        notes = [
            f"missing edge case, not covered by any approved scenario: {case}"
            for case in self._required_edge_cases
            if case.lower() not in covered_text
        ]

        return ReviewResult(approved=approved, rejected=rejected, notes=notes)
