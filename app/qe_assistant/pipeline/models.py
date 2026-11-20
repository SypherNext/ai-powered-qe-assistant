"""Plain data passed between pipeline stages. No behavior here on purpose.

NOTE on a real contract bug found while assembling this repo: the
Protocol sketches in the "AI-Powered QE Assistant" lesson originally
declared TestExecutor.execute() -> ExecutionResult (singular) and
FailureAnalyzer.analyze(execution_result: ExecutionResult) -> AnalysisResult
(singular), and QEReportBuilder.build(review, guardrails, execution,
analysis) -> Report. The actual implementations below -- and the
Capstone lesson's own worked implementations -- return/accept *lists* of
ExecutionResult/AnalysisResult, and QEReportBuilder.build() takes
(requirement, review, guardrails, analysis) with no separate `execution`
argument at all (the executor's results are already folded into
`analysis` by the time the report builder runs). The interface sketch
and the real implementation disagreed with each other. This repo follows
the real, working implementation; the data-fix applied to the lesson
corrects the sketch to match it.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class TestScenario:
    title: str
    setup: str
    expected_outcome: str


@dataclass
class ReviewResult:
    approved: list[TestScenario]
    rejected: list[tuple[TestScenario, str]]
    notes: list[str]


@dataclass
class GuardrailResult:
    passed: bool
    failed_criteria: list[str]


@dataclass
class ExecutionResult:
    scenario_title: str
    passed: bool
    run_history: list[bool]
    error_message: str | None = None


@dataclass
class AnalysisResult:
    scenario_title: str
    verdict: str  # "passed" | "stale_test" | "real_bug"
    confidence: float
    reasoning: str


@dataclass
class Report:
    requirement: str
    approved_scenario_count: int
    rejected_scenario_count: int
    guardrail_passed: bool
    findings: list[AnalysisResult]
    as_markdown: str
