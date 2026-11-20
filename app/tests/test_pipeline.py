"""End-to-end capstone pipeline tests. See the "Capstone: AI-Powered QE
Assistant" lesson. Everything here runs against RecordedProvider /
RecordedExecutor -- no live model call, no real browser, $0 cost.

test_golden_set_regression_against_recorded_provider is this repo's
golden-set-style regression test: it re-runs the full pipeline against a
fixed, checked-in scenario batch and asserts the shape of the result
hasn't drifted -- the same role a scheduled live-model run plays in
production, just using a recorded response so it's free and
deterministic to run here.
"""

import json

import pytest

from qe_assistant.llm_provider import LLMProvider, RecordedProvider
from qe_assistant.pipeline.analyzer import HeuristicFailureAnalyzer
from qe_assistant.pipeline.automation_generator import AnthropicAutomationGenerator
from qe_assistant.pipeline.executor import RecordedExecutor
from qe_assistant.pipeline.generator import AnthropicTestGenerator
from qe_assistant.pipeline.models import ExecutionResult
from qe_assistant.pipeline.orchestrator import run_qe_pipeline
from qe_assistant.pipeline.quality_gate import LintGuardrailChecker
from qe_assistant.pipeline.report_builder import MarkdownReportBuilder
from qe_assistant.pipeline.reviewer import ChecklistTestReviewer


SLA_REQUIREMENT = (
    "SLA Auto-Escalation: when a ticket's SLA countdown reaches 60 minutes remaining "
    "and the ticket is still status \"Open\" with no recent agent activity, the system "
    "bumps priority to \"Urgent\", sets escalated_by_system to true, and notifies the "
    "assigned agent's team channel via Slack."
)

SLA_GENERATOR_RESPONSE = json.dumps([
    {"title": "SLA breach on an eligible ticket escalates correctly",
     "setup": "status Open, no recent agent activity, SLA countdown reaches 60 minutes",
     "expected_outcome": 'priority becomes "Urgent", escalated_by_system becomes true, one Slack message sent'},
    {"title": "Already-Urgent ticket does not double-escalate",
     "setup": "ticket already priority Urgent at the 60-minute mark",
     "expected_outcome": "no field changes, no new Slack message"},
    {"title": "duplicate of the first scenario",
     "setup": "status Open, no recent agent activity, SLA countdown reaches 60 minutes",
     "expected_outcome": "the ticket updates and the agent is notified"},
])

SLA_AUTOMATION_RESPONSE = (
    "import { test, expect } from '../fixtures';\n"
    "test('SLA breach escalates', async ({ seedTicket, page }) => {\n"
    "  const ticket = await seedTicket({ status: 'Open', minutesToBreach: 61 });\n"
    "  await page.goto(`/dashboard/tickets/${ticket.id}`);\n"
    "  await expect(page.getByTestId('ticket-priority-badge')).toHaveText('Urgent');\n"
    "});\n"
)

REQUIRED_EDGE_CASES = [
    "no assigned agent", "resolved before breach", "multiple simultaneous breaches",
    "waiting on customer", "already urgent",
]


def build_pipeline_kwargs(generator_response: str, automation_response: str, required_edge_cases: list[str],
                           execution_results: list[ExecutionResult]) -> dict:
    return dict(
        generator=AnthropicTestGenerator(RecordedProvider(generator_response)),
        reviewer=ChecklistTestReviewer(required_edge_cases=required_edge_cases),
        automation_generator=AnthropicAutomationGenerator(RecordedProvider(automation_response)),
        guardrail_checker=LintGuardrailChecker(),
        executor=RecordedExecutor(execution_results),
        analyzer=HeuristicFailureAnalyzer(),
        report_builder=MarkdownReportBuilder(),
    )


def test_full_pipeline_against_sla_auto_escalation():
    report = run_qe_pipeline(
        requirement=SLA_REQUIREMENT,
        **build_pipeline_kwargs(
            SLA_GENERATOR_RESPONSE,
            SLA_AUTOMATION_RESPONSE,
            REQUIRED_EDGE_CASES,
            [ExecutionResult("SLA breach on an eligible ticket escalates correctly", True, [True, True, True])],
        ),
    )

    # The reviewer must have caught the duplicate -- 2 approved, 1 rejected.
    assert report.approved_scenario_count == 2
    assert report.rejected_scenario_count == 1
    assert report.guardrail_passed is True
    assert len(report.findings) == 1
    assert report.findings[0].verdict == "passed"
    assert "SLA Auto-Escalation" in report.as_markdown


def test_guardrail_failure_blocks_execution_and_analysis():
    """If GuardrailChecker fails, TestExecutor must never run -- this is
    the orchestrator's one load-bearing conditional."""
    automation_with_secret = (
        "import { test, expect } from '@playwright/test';\n"
        "test('t', async ({ request }) => {\n"
        "  await request.post('/x', { headers: { Authorization: 'Bearer sk-fake-1234567890abcdef' } });\n"
        "  expect(true).toBeTruthy();\n"
        "});\n"
    )
    report = run_qe_pipeline(
        requirement=SLA_REQUIREMENT,
        **build_pipeline_kwargs(
            SLA_GENERATOR_RESPONSE, automation_with_secret, REQUIRED_EDGE_CASES,
            [ExecutionResult("should never run", True, [True])],
        ),
    )

    assert report.guardrail_passed is False
    assert report.findings == [], "analysis must not run when the guardrail gate failed"


def test_golden_set_regression_against_recorded_provider():
    """Golden-set-style regression test: fixed input, fixed recorded
    response, asserts the pipeline's structural output hasn't drifted.
    This plays the same role Module 6's live-model golden set plays in
    production, except it's deterministic and free to run in CI."""
    report = run_qe_pipeline(
        requirement=SLA_REQUIREMENT,
        **build_pipeline_kwargs(
            SLA_GENERATOR_RESPONSE,
            SLA_AUTOMATION_RESPONSE,
            REQUIRED_EDGE_CASES,
            [ExecutionResult("SLA breach on an eligible ticket escalates correctly", True, [True, True, True])],
        ),
    )

    golden_shape = {
        "approved_scenario_count": 2,
        "rejected_scenario_count": 1,
        "guardrail_passed": True,
        "finding_verdicts": ["passed"],
    }
    assert report.approved_scenario_count == golden_shape["approved_scenario_count"]
    assert report.rejected_scenario_count == golden_shape["rejected_scenario_count"]
    assert report.guardrail_passed == golden_shape["guardrail_passed"]
    assert [f.verdict for f in report.findings] == golden_shape["finding_verdicts"]


def test_pipeline_reusable_against_a_second_unrelated_requirement():
    """The capstone's reusability exercise: the exact same reviewer,
    guardrail checker, and analyzer classes -- unmodified -- must handle a
    completely different requirement correctly. Only configuration
    (required_edge_cases) changes."""
    bulk_tag_requirement = (
        "Bulk Ticket Tagging: support agents can select multiple tickets in the "
        "dashboard and apply a tag to all of them at once; a tag already present on "
        "some but not all selected tickets should not be duplicated on the tickets "
        "that already have it."
    )
    generator_response = json.dumps([
        {"title": "Tag applied to all selected tickets",
         "setup": "three tickets selected, none have the tag yet",
         "expected_outcome": 'each of the three tickets gains the tag "needs-follow-up"'},
        {"title": "Tag not duplicated on a ticket that already has it",
         "setup": "two tickets selected, one already tagged \"vip\", one not",
         "expected_outcome": 'the already-tagged ticket keeps exactly one "vip" tag, the other gains one'},
        {"title": "Vague tagging scenario", "setup": "tickets selected and tag applied",
         "expected_outcome": "it works"},
    ])
    automation_response = (
        "import { test, expect } from '../fixtures';\n"
        "test('bulk tag apply', async ({ page }) => {\n"
        "  await expect(page.getByTestId('tag-chip')).toHaveText('vip');\n"
        "});\n"
    )

    report = run_qe_pipeline(
        requirement=bulk_tag_requirement,
        **build_pipeline_kwargs(
            generator_response, automation_response,
            required_edge_cases=["tag already present", "multiple tickets selected"],
            execution_results=[ExecutionResult("Tag applied to all selected tickets", True, [True])],
        ),
    )

    # The vague third scenario must still be caught -- same reviewer, new domain.
    assert report.rejected_scenario_count == 1
    assert report.approved_scenario_count == 2
    assert report.guardrail_passed is True


def test_reviewer_and_guardrail_checker_never_import_llm_provider():
    """Structural assertion, not just a style claim: TestReviewer and
    GuardrailChecker must have zero dependency on LLMProvider anywhere in
    their module."""
    from qe_assistant.pipeline import quality_gate, reviewer

    for module in (reviewer, quality_gate):
        assert "LLMProvider" not in dir(module)
        assert not any("llm_provider" in name for name in dir(module))
