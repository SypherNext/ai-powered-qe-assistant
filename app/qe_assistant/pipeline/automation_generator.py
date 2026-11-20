"""AutomationGenerator -- AI-driven, has no knowledge of GuardrailChecker's
rules. See the AI-Powered QE Assistant / Capstone lessons."""

from __future__ import annotations

from ..llm_provider import LLMProvider
from .models import TestScenario

AUTOMATION_SYSTEM_PROMPT = """\
You are a Playwright TypeScript test generator. Given approved QE \
scenarios, write one @playwright/test file that automates all of them. \
Use data-testid locators and Playwright's built-in retrying assertions \
(toHaveText, expect.poll) -- never waitForTimeout. Never hardcode a \
secret or credential. Respond with TypeScript source only.
"""


class AnthropicAutomationGenerator:
    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    def generate(self, scenarios: list[TestScenario]) -> str:
        scenario_text = "\n".join(f"- {s.title}: {s.setup} -> {s.expected_outcome}" for s in scenarios)
        return self._provider.complete(AUTOMATION_SYSTEM_PROMPT, scenario_text)
