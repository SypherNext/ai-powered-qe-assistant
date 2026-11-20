"""Prompt-shape and output-validation tests for the Ticket Summarizer.
See the "Testing LLM Applications" lesson. Every test uses RecordedProvider
-- no real API call, no cost."""

import json

import pytest

from qe_assistant.llm_provider import RecordedProvider
from qe_assistant.ticket_summarizer import summarize_ticket


def make_provider(summary: str, sentiment: str, suggested_next_action: str) -> RecordedProvider:
    return RecordedProvider(json.dumps({
        "summary": summary,
        "sentiment": sentiment,
        "suggested_next_action": suggested_next_action,
    }))


# --- Prompt-shape tests ------------------------------------------------------

def test_returns_valid_json_with_exactly_the_contract_fields():
    provider = make_provider(
        "Customer's CSV export of the monthly billing report has been stuck processing for 20 minutes.",
        "neutral",
        "Check the export job queue for a stuck job on this account.",
    )
    result = summarize_ticket("some thread", provider)

    assert set(result.keys()) == {"summary", "sentiment", "suggested_next_action"}


@pytest.mark.parametrize("sentiment", ["frustrated", "neutral", "satisfied"])
def test_sentiment_stays_within_allowed_values(sentiment):
    provider = make_provider("summary text", sentiment, "do something")
    result = summarize_ticket("some thread", provider)
    assert result["sentiment"] in ("frustrated", "neutral", "satisfied")


def test_malformed_json_raises_instead_of_silently_passing():
    provider = RecordedProvider("not json at all")
    with pytest.raises(json.JSONDecodeError):
        summarize_ticket("some thread", provider)


# --- Output-validation style checks (hallucination / factuality) -----------

def test_golden_case_csv_export_stuck_summary_is_grounded():
    """A golden-set-style case: given a known thread, the summary must not
    invent anything the thread doesn't say."""
    thread = (
        "Customer: My export to CSV has been stuck at 'Processing' for 20 minutes. "
        "Agent: Can you tell me which report you're exporting? "
        "Customer: The monthly billing report."
    )
    provider = make_provider(
        "Customer's CSV export of the monthly billing report has been stuck processing for 20 minutes.",
        "neutral",
        "Check the export job queue for a stuck job on this account.",
    )
    result = summarize_ticket(thread, provider)

    # Nothing in the summary should mention a dollar figure, an order
    # number, or a promise that never appeared in the thread.
    assert "refund" not in result["summary"].lower()
    assert "order #" not in result["summary"].lower()
