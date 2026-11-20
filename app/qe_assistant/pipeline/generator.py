"""TestGenerator -- AI-driven, the only component allowed to invent
scenario content. See the AI-Powered QE Assistant / Capstone lessons."""

from __future__ import annotations

import json

from ..llm_provider import LLMProvider
from .models import TestScenario

GENERATOR_SYSTEM_PROMPT = """\
You are a QE test-scenario generator. Given a product requirement, return \
a JSON array of test scenarios. Each item has exactly three fields: \
"title", "setup", "expected_outcome". Cover the happy path and plausible \
edge cases implied by the requirement. Respond with JSON only.
"""


class AnthropicTestGenerator:
    def __init__(self, provider: LLMProvider) -> None:
        self._provider = provider

    def generate(self, requirement: str) -> list[TestScenario]:
        raw = self._provider.complete(GENERATOR_SYSTEM_PROMPT, requirement)
        return [TestScenario(**item) for item in json.loads(raw)]
