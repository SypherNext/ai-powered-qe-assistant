"""The LLMProvider abstraction every AI-systems-under-test lesson builds on.

One provider protocol, two implementations:

- AnthropicProvider: the real provider. Reads ANTHROPIC_API_KEY from the
  environment -- never hardcoded, never checked into a fixture. Used in
  production and in the occasional scheduled golden-set regression run.
- RecordedProvider: a test double that replays a fixed response. Used for
  every test in this repo so the suite is fast, deterministic, and free.
"""

from __future__ import annotations

import os
from typing import Protocol


class LLMProvider(Protocol):
    def complete(self, system_prompt: str, user_prompt: str) -> str:
        """Return the raw text completion for a system/user prompt pair."""
        ...


class AnthropicProvider:
    """Real provider -- used in production and in live smoke tests.

    Bug fixed here versus the lesson's first-draft snippet: the original
    code read `response.content[0].text` directly. That crashes with an
    AttributeError whenever the API returns a non-text content block
    (a thinking block, for instance) ahead of the text block. This joins
    every text-type block instead, which is correct regardless of what
    else is in the response.
    """

    def __init__(self, model: str = "claude-sonnet-5-5") -> None:
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        # Import kept local so the rest of this package has no hard
        # dependency on the anthropic SDK being installed.
        import anthropic

        self._client = anthropic.Anthropic(api_key=api_key)
        self._model = model

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        response = self._client.messages.create(
            model=self._model,
            max_tokens=512,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}],
        )
        return "".join(
            block.text for block in response.content if getattr(block, "type", None) == "text"
        )


class RecordedProvider:
    """Test double -- replays a fixed response instead of calling a model.

    Used for prompt-shape tests where the point is to check how the
    calling code handles a response, not to re-verify the model itself.
    """

    def __init__(self, response_text: str) -> None:
        self._response_text = response_text

    def complete(self, system_prompt: str, user_prompt: str) -> str:
        return self._response_text
