"""AI-Powered QE Assistant — reference implementation.

Companion project for the "AI for Quality Engineering" course. Everything
in this package traces back to a specific lesson:

- llm_provider      -> AI-Powered QE: the Ticket Summarizer lesson
- ticket_summarizer  -> the Ticket Summarizer lesson
- knowledge_assistant -> the RAG Evaluation lesson
- guardrails         -> the AI Security lesson
- triage_agent       -> the AI Agent Testing lesson
- pipeline/*         -> the AI-Powered QE Assistant + Capstone lessons

No network call happens anywhere in this package unless a caller
explicitly constructs AnthropicProvider with a real API key. Every test in
tests/ uses RecordedProvider / RecordedRetriever / RecordedTools / a
scripted provider stand-in instead, so the full suite runs for $0.
"""
