"""Vespera's Knowledge Assistant: Ticket Summarizer plus retrieval.

Extends ticket_summarizer's contract with two new fields (draft_answer,
citations), backed by a small, swappable Retriever abstraction. See the
"RAG Evaluation" lesson.
"""

from __future__ import annotations

import json
from typing import Protocol

from .llm_provider import LLMProvider

KNOWLEDGE_ASSISTANT_SYSTEM_PROMPT = """\
You are Vespera Helpdesk's knowledge assistant. You will be given a support \
ticket thread and a set of retrieved knowledge-base articles that may be \
relevant to it.

Rules:
- Summarize only what is explicitly present in the thread. Never invent \
details that are not there.
- Base "draft_answer" only on the retrieved articles provided to you. Do \
not use outside knowledge, and do not state anything as policy unless a \
retrieved article actually supports it.
- Every claim in "draft_answer" that depends on a retrieved article must \
be attributable to one of the article IDs listed in "citations". Do not \
cite an article that does not support the specific claim it's attached to.
- "draft_answer" is a draft for a human agent to review and send -- it is \
never sent automatically, and it must not claim an action (like a refund) \
has already happened.
- Respond with JSON only, using exactly these fields: "summary", \
"sentiment", "suggested_next_action", "draft_answer", "citations". No \
extra fields, no prose outside the JSON.
"""


class Retriever(Protocol):
    def retrieve(self, query: str, top_k: int = 3) -> list[str]:
        """Return up to top_k KB article IDs relevant to the query, ranked."""
        ...


KNOWLEDGE_BASE: dict[str, dict] = {
    "KB-1042": {
        "title": "How to reset your password",
        "content": (
            "To reset your password, go to Account Settings > Security. "
            "If you're locked out of your account, support can verify your "
            "identity and issue a new reset link. This process does not "
            "affect your billing or subscription status."
        ),
    },
    "KB-2210": {
        "title": "Refund eligibility policy",
        "content": (
            "Cancellations submitted within 7 days of the renewal charge "
            "are eligible for a full refund of that charge, processed "
            "automatically within 5 business days. Cancellations submitted "
            "after 7 days require Team Lead approval."
        ),
    },
    "KB-3301": {
        "title": "CSV export stuck on Processing",
        "content": (
            "If a report export stays on 'Processing' for more than 10 "
            "minutes, it usually means the export job is stuck in the "
            "queue. Restarting the export from the report page clears "
            "most stuck jobs; if it recurs, escalate to engineering."
        ),
    },
}


class KeywordRetriever:
    """Toy retriever: ranks KB articles by keyword overlap with the query.

    Vespera's real retriever uses an embedding index; this keeps the
    retrieval-evaluation code runnable without a vector database
    dependency. The evaluation approach doesn't care which retriever
    implementation is behind the Retriever protocol.
    """

    def __init__(self, knowledge_base: dict[str, dict]) -> None:
        self._kb = knowledge_base

    def retrieve(self, query: str, top_k: int = 3) -> list[str]:
        query_words = set(query.lower().split())
        scored = []
        for article_id, article in self._kb.items():
            article_words = set(article["content"].lower().split())
            overlap = len(query_words & article_words)
            if overlap > 0:
                scored.append((overlap, article_id))
        scored.sort(reverse=True)
        return [article_id for _, article_id in scored[:top_k]]


class RecordedRetriever:
    """Test double -- always returns a fixed list of article IDs.

    Same role as RecordedProvider: it lets you test the code that
    *consumes* retrieval results without depending on real retrieval
    quality, which is evaluated separately (see tests/test_knowledge_assistant.py).
    """

    def __init__(self, article_ids: list[str]) -> None:
        self._article_ids = article_ids

    def retrieve(self, query: str, top_k: int = 3) -> list[str]:
        return self._article_ids[:top_k]


def answer_with_knowledge(
    thread: str,
    retriever: Retriever,
    provider: LLMProvider,
    knowledge_base: dict[str, dict] = KNOWLEDGE_BASE,
    top_k: int = 3,
) -> dict:
    retrieved_ids = retriever.retrieve(thread, top_k=top_k)
    retrieved_context = "\n\n".join(
        f"[{article_id}] {knowledge_base[article_id]['title']}\n"
        f"{knowledge_base[article_id]['content']}"
        for article_id in retrieved_ids
        if article_id in knowledge_base
    )
    user_prompt = f"Ticket thread:\n{thread}\n\nRetrieved articles:\n{retrieved_context}"
    raw = provider.complete(KNOWLEDGE_ASSISTANT_SYSTEM_PROMPT, user_prompt)
    result = json.loads(raw)
    result["_retrieved_ids"] = retrieved_ids  # kept for evaluation, not shown to the agent
    return result


def recall_at_k(golden_set: list[tuple[str, list[str]]], retriever: Retriever, k: int = 3) -> float:
    """Deterministic retrieval-evaluation metric -- no model call at all.

    golden_set is a list of (query, expected_relevant_article_ids) pairs.
    Returns the average fraction of each case's expected IDs that showed
    up in the retriever's top-k results.
    """
    if not golden_set:
        return 0.0
    scores = []
    for query, expected_ids in golden_set:
        retrieved = set(retriever.retrieve(query, top_k=k))
        expected = set(expected_ids)
        if not expected:
            continue
        scores.append(len(expected & retrieved) / len(expected))
    return sum(scores) / len(scores) if scores else 0.0
