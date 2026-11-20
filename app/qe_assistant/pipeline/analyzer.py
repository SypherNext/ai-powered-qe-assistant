"""FailureAnalyzer -- deterministic in this simplified implementation,
formalizing the AI Test Maintenance lesson's stale-test-vs-real-bug
diagnostic heuristic. "AI-assisted" in the lesson describes the *kind* of
judgment being formalized, not a requirement that every implementation
literally calls a model."""

from __future__ import annotations

from .models import AnalysisResult, ExecutionResult


class HeuristicFailureAnalyzer:
    """Confidence is deliberately kept below 1.0 for anything that isn't
    a clean pass -- a QE overriding this verdict is the expected path,
    not an edge case."""

    def analyze(self, results: list[ExecutionResult]) -> list[AnalysisResult]:
        findings = []
        for result in results:
            if result.passed and all(result.run_history):
                findings.append(AnalysisResult(result.scenario_title, "passed", 1.0, "consistently green"))
                continue

            intermittent = len(set(result.run_history)) > 1
            if intermittent:
                findings.append(AnalysisResult(
                    result.scenario_title, "real_bug", 0.7,
                    "Intermittent across runs -- usually means a live, timing-dependent bug, not test "
                    "flakiness. A QE must trace the actual mechanism before this verdict is trusted.",
                ))
            else:
                findings.append(AnalysisResult(
                    result.scenario_title, "stale_test", 0.6,
                    "Consistently failing, not intermittent -- check for a changed selector or renamed "
                    "component before assuming this is a product bug.",
                ))
        return findings
