"""GuardrailChecker -- deterministic static analysis, the Test Guardrails
lesson's six-item quality gate and secret scanner, applied to generated
automation code rather than scenario text. No LLMProvider import here
either -- a genuinely separate code path from reviewer.py, even though
both produce a pass/fail-with-reasons verdict."""

from __future__ import annotations

import re

from .models import GuardrailResult

SECRET_PATTERNS = [
    re.compile(r"""['"`]sk-[A-Za-z0-9]{16,}['"`]"""),
    re.compile(r"""Authorization\s*[:=]\s*['"`]Bearer\s+[A-Za-z0-9_\-.]{10,}['"`]"""),
]


class LintGuardrailChecker:
    def check(self, automation_code: str) -> GuardrailResult:
        failed: list[str] = []

        if any(pattern.search(automation_code) for pattern in SECRET_PATTERNS):
            failed.append("hardcoded secret detected")
        if "waitForTimeout" in automation_code:
            failed.append("arbitrary sleep (waitForTimeout) present")
        if re.search(r"""\.locator\(['"]\.css-""", automation_code):
            failed.append("brittle auto-generated CSS class selector")
        if "data-testid" not in automation_code and "getByTestId" not in automation_code:
            failed.append("no data-testid-based selector found")
        if "expect(" not in automation_code:
            failed.append("no assertions found")

        return GuardrailResult(passed=len(failed) == 0, failed_criteria=failed)
