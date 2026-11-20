"""The thin orchestrator -- the whole point of the AI-Powered QE
Assistant / Capstone lessons. Read it and check: is there a single line
here that decides whether a scenario or a fix is correct? There isn't --
every real verdict happens inside a component, never in this function."""

from __future__ import annotations

from typing import Protocol

from .models import AnalysisResult, ExecutionResult, GuardrailResult, Report, ReviewResult, TestScenario


class TestGenerator(Protocol):
    def generate(self, requirement: str) -> list[TestScenario]: ...


class TestReviewer(Protocol):
    def review(self, scenarios: list[TestScenario]) -> ReviewResult: ...


class GuardrailChecker(Protocol):
    def check(self, automation_code: str) -> GuardrailResult: ...


class AutomationGenerator(Protocol):
    def generate(self, scenarios: list[TestScenario]) -> str: ...


class TestExecutor(Protocol):
    def execute(self, automation_code: str) -> list[ExecutionResult]: ...


class FailureAnalyzer(Protocol):
    def analyze(self, results: list[ExecutionResult]) -> list[AnalysisResult]: ...


class QEReportBuilder(Protocol):
    def build(
        self, requirement: str, review: ReviewResult, guardrails: GuardrailResult, analysis: list[AnalysisResult]
    ) -> Report: ...


def run_qe_pipeline(
    requirement: str,
    generator: TestGenerator,
    reviewer: TestReviewer,
    automation_generator: AutomationGenerator,
    guardrail_checker: GuardrailChecker,
    executor: TestExecutor,
    analyzer: FailureAnalyzer,
    report_builder: QEReportBuilder,
) -> Report:
    scenarios = generator.generate(requirement)
    review = reviewer.review(scenarios)

    automation_code = automation_generator.generate(review.approved)
    guardrails = guardrail_checker.check(automation_code)

    execution_results = executor.execute(automation_code) if guardrails.passed else []
    analysis = analyzer.analyze(execution_results) if execution_results else []

    return report_builder.build(requirement, review, guardrails, analysis)
