# Implementation review

## Stage 1 — Configuration and provider
- Review: SDK imports are lazy; offline execution does not create a model or require keys. Paths derive from repository root; compact settings are validated.
- Counterargument: installed SDKs do not prove live connectivity. Live API smoke tests require credentials and are outside deterministic verification; model names are configurable.
- Validation: compilation and offline configuration smoke test.

## Stage 2 — Memory
- Review: hashed user IDs prevent traversal and collisions; atomic replacement persists UTF-8 profiles; keyed updates replace outdated facts; summaries have a bounded budget.
- Counterargument: regex extraction and excerpt summaries are deliberately limited. They cannot establish truth for arbitrary language; recent oversized messages may exceed threshold. Tests will cover supplied corrections and noise; semantic summarization remains a live-mode extension.
- Validation: profile persistence, correction and repeated compaction smoke checks passed.

## Stage 3 — Agents
- Review: both agents share extraction and response logic, so baseline is capable within a thread. Advanced persists facts and includes profile, summary and recent messages in accounting. Thread owner checks prevent cross-user reuse.
- Counterargument: offline responses measure memory plumbing, not LLM intelligence or style compliance. Live uses direct chat invocation, not optional LangGraph tooling; token totals remain heuristic estimates. No live API calls were made.
- Validation: same-thread baseline recall, fresh-thread forgetting, advanced recall after restart passed.
