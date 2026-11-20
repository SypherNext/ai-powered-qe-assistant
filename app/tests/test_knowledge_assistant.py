"""Retrieval and generation evaluation for the Knowledge Assistant. See the
"RAG Evaluation" lesson -- retrieval and generation are scored on
independent paths."""

import json

from qe_assistant.knowledge_assistant import (
    KNOWLEDGE_BASE,
    KeywordRetriever,
    RecordedRetriever,
    answer_with_knowledge,
    recall_at_k,
)
from qe_assistant.llm_provider import RecordedProvider


# --- Retrieval evaluation (no model call at all) ----------------------------

def test_keyword_retriever_recall_on_golden_set():
    retriever = KeywordRetriever(KNOWLEDGE_BASE)
    golden_set = [
        ("My CSV export has been stuck on Processing for a while", ["KB-3301"]),
        ("I need to reset my password, I'm locked out", ["KB-1042"]),
    ]
    score = recall_at_k(golden_set, retriever, k=3)
    assert score == 1.0


def test_recorded_retriever_is_deterministic_for_generation_tests():
    retriever = RecordedRetriever(["KB-2210"])
    assert retriever.retrieve("anything") == ["KB-2210"]
    assert retriever.retrieve("anything else") == ["KB-2210"]


# --- Generation evaluation (isolated from retrieval quality) ---------------

def test_answer_only_cites_ids_that_were_actually_retrieved():
    retriever = RecordedRetriever(["KB-2210"])
    provider = RecordedProvider(json.dumps({
        "summary": "Customer wants a refund for a charge after cancelling.",
        "sentiment": "neutral",
        "suggested_next_action": "Review the refund eligibility window.",
        "draft_answer": "Since you cancelled within 7 days, you're eligible for a full refund.",
        "citations": ["KB-2210"],
    }))

    result = answer_with_knowledge("ticket thread", retriever, provider)

    assert result["_retrieved_ids"] == ["KB-2210"]
    for citation in result["citations"]:
        assert citation in result["_retrieved_ids"], (
            "a model citing an article it was never given is a clear-cut "
            "failure that shouldn't need an LLM judge to catch"
        )


def test_citation_pointing_at_an_unretrieved_article_is_detectable():
    """Mechanical pre-check: cheap and deterministic, catches a citation
    that wasn't even in the retrieved set -- the kind of check that
    should never need an LLM judge."""
    retriever = RecordedRetriever(["KB-3301"])
    provider = RecordedProvider(json.dumps({
        "summary": "s", "sentiment": "neutral", "suggested_next_action": "a",
        "draft_answer": "Your refund is being processed.",
        "citations": ["KB-2210"],  # never retrieved
    }))

    result = answer_with_knowledge("ticket thread", retriever, provider)

    bad_citations = [c for c in result["citations"] if c not in result["_retrieved_ids"]]
    assert bad_citations == ["KB-2210"]
