"""QEReportBuilder -- deterministic, adds no judgment of its own. Assembles
every prior stage's output into one QE-facing artifact."""

from __future__ import annotations

from .models import AnalysisResult, GuardrailResult, Report, ReviewResult


class MarkdownReportBuilder:
    def build(
        self,
        requirement: str,
        review: ReviewResult,
        guardrails: GuardrailResult,
        analysis: list[AnalysisResult],
    ) -> Report:
        lines = [
            f"# QE Report -- {requirement.splitlines()[0][:70]}",
            "",
            f"- Approved scenarios: {len(review.approved)}",
            f"- Rejected scenarios: {len(review.rejected)}",
            f"- Guardrail check: {'PASSED' if guardrails.passed else 'FAILED -- ' + ', '.join(guardrails.failed_criteria)}",
            "",
            "## Findings",
        ]
        for finding in analysis:
            lines.append(f"- **{finding.scenario_title}** -- {finding.verdict} (confidence {finding.confidence}): {finding.reasoning}")

        markdown = "\n".join(lines)
        return Report(
            requirement=requirement,
            approved_scenario_count=len(review.approved),
            rejected_scenario_count=len(review.rejected),
            guardrail_passed=guardrails.passed,
            findings=analysis,
            as_markdown=markdown,
        )
