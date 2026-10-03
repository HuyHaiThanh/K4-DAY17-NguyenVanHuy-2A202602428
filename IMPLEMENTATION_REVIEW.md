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

## Stage 4 — Benchmark and tests
- Review: fresh recall thread per question; immediate evaluation after each conversation; temporary clean state; counters summed once per thread; both training and recall costs included.
- Counterargument: substring recall can reward echoed facts and quality is not independent. Baseline may obtain a small nonzero score from facts explicitly embedded in questions. We retain the supplied scoring protocol and disclose it rather than forcing baseline to zero.
- Failures found and fixed: question text overwrote name; joke overwrote profession; comma-separated interests lost AI; later interests replaced earlier ones.
- Validation: 7 behavioral tests passed, including both full datasets, restart, user isolation, correction/noise and long-context savings.

## Stage 5 — Final review and submission
- Review: report distinguishes token estimates, recall and quality proxy; records Windows commands and live scope. READMEs identify completed implementation.
- Counterargument: perfect small-dataset recall is not production readiness; semantic summaries, concurrent writes, preference deletion and live usage accounting remain documented limitations.
- Validation: 7 tests passed; two clean benchmark runs identical; git diff --check passed. Submission targets origin/main, not upstream.

## Compatibility correction after user review
- Finding: AgentContext and force_offline were removed; default construction required remote credentials; hashed-only paths diverged from the documented layout. These were genuine compatibility risks.
- Fix: restore original declarations, annotations, dataclass fields and method order; offline fallback without credentials; safe user path and legacy hashed-profile reads; tolerate plain Markdown fact values.
- Counterargument: hidden tests are unavailable. Snapshot checks establish published declaration compatibility, not arbitrary hidden expectations or production language coverage. Additional helper methods/files remain implementation details.
- Validation: 11 tests passed, including AST declaration snapshot derived from dc0e2da; benchmark output unchanged; diff whitespace checks passed.

## Guide steps and bonus audit (2026-10-03)
- Review: steps 1–8 are implemented for offline scope; selected step 9 work is structured fields, correction/conflict handling and rule-based question/noise filtering. Evidence and limits are in STEP9.md.
- Counterargument: these heuristics overlap core extraction and do not establish a calibrated confidence threshold or decay. No ablation measures incremental bonus gain; no promise of a numeric grade or hidden-test success.
- Validation: reran full suite: 11 passed; both benchmark tables unchanged. No implementation changes in this audit.

## Step 9 implementation — confidence gate
- Implementation: ProfileMemoryPolicy applies configurable finite threshold before profile writes, sentence-level evidence scores and decision reasons; uncertain candidates do not re-enter offline facts from recent context. Scaffold declarations unchanged.
- Review: questions remain rejected even at zero threshold; explicit corrections accepted; uncertainty survives restart as a rejected write. Ablation at 0.8 vs 0.4 demonstrates prevention of uncertain-location overwrite.
- Counterargument: scores are policy weights, not calibrated probabilities; strict thresholds may suppress true facts. No memory decay or semantic truth verification claimed.
- Regression fixed: treating every mention of examples as hypothetical suppressed valid style preferences; narrowed the hypothetical marker and added a regression test.
- Validation: 26 tests passed including original API contract; two original datasets retain Advanced 100% recall; updated stress metrics reflect gated context (312 output / 11043 prompt).

## Step 9 continuation — persistent memory decay
- Implementation: metadata sidecar records accepted fact value, last assertion time and confirmation count; half-life priority filters persistent retrieval; name/unknown-age legacy facts are protected. Reconfirmation refreshes; corrections reset count. Questions/rejected facts never refresh timestamps. Original API signatures unchanged; memory_file_size keeps profile-only meaning, optional memory_storage_size includes sidecar for benchmark.
- Review: fake-clock tests establish lower prompt load and stale-profile exclusion after restart; retention/reconfirmation and bounded reinforcement tested; raw profile is not deleted. Decay demo documents time-based behavior independently of the fast original benchmark.
- Counterargument: age alone cannot determine truth; valid old facts may be suppressed. Ongoing thread messages can still contain old facts. Two-file atomic replacement is not a shared transaction or concurrent-writer lock. Sidecar increases disk usage, explicitly included in growth metrics.
- Validation: 37 tests passed; original declaration contract passed; two fresh benchmark runs identical with 100% Advanced recall; growth 957/647 bytes includes sidecar.
