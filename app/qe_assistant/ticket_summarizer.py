"""Vespera Helpdesk's first AI feature: the Ticket Summarizer.

Given a ticket thread, returns a small JSON object a support agent sees
at the top of the ticket view before reading the full thread. See the
"Testing LLM Applications" lesson.
"""

from __future__ import annotations

import json

from .llm_provider import LLMProvider

SYSTEM_PROMPT = """\
You are Vespera Helpdesk's ticket summarizer. You will be given a support \
ticket thread containing customer messages and agent replies.

Rules:
- Summarize only what is explicitly present in the thread. Never invent \
details that are not there -- no order numbers, dates, product names, or \
promises that were not actually made.
- If the customer's tone in the thread sounds frustrated, set "sentiment" \
to "frustrated". Otherwise use "neutral" or "satisfied", whichever fits \
better.
- Never recommend a refund or any account action yourself (e.g. "issue a \
refund," "close the account," "waive the fee"). That decision always \
stays with the human agent -- at most, suggest that the agent review the \
account.
- Respond with JSON only, using exactly these fields: "summary", \
"sentiment", "suggested_next_action". No extra fields, no prose outside \
the JSON.
"""


def summarize_ticket(thread: str, provider: LLMProvider) -> dict:
    raw = provider.complete(SYSTEM_PROMPT, thread)
    return json.loads(raw)
