# Implemented lab

All nine Guide steps are implemented: offline/live agents, LangGraph checkpoints and guarded tools, dynamic profile prompt, model-based live summarization, confidence gate, decay, two benchmarks and optional semantic judge.

From root: python -m pytest src -v; python src/benchmark.py; python src/benchmark_decay.py. Live: python src/benchmark.py --live --judge with credentials. See ../REPORT.md and ../COMPLETION.md for evidence and verification limits.
