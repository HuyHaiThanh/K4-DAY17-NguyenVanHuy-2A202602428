from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

from agent_advanced import AdvancedAgent
from agent_baseline import BaselineAgent
from config import load_config

from dataclasses import dataclass, replace
import json
import tempfile


@dataclass
class BenchmarkRow:
    agent_name: str
    agent_tokens_only: int
    prompt_tokens_processed: int
    recall_score: float
    response_quality: float
    memory_growth_bytes: int
    compactions: int


def load_conversations(path: Path) -> list[dict[str, Any]]:
    """Student TODO: read JSON conversations from disk."""

    return json.loads(path.read_text(encoding='utf-8'))


def recall_points(answer: str, expected: list[str]) -> float:
    """Student TODO: return 0 / 0.5 / 1 depending on how many expected facts appear."""

    if not expected:
        return 1.0
    hits = sum(value.casefold() in answer.casefold() for value in expected)
    return 1.0 if hits == len(expected) else 0.5 if hits else 0.0


def heuristic_quality(answer: str, expected: list[str]) -> float:
    """Student TODO: add a lightweight quality score for offline mode."""

    return recall_points(answer, expected) * (1.0 if 0 < len(answer) <= 600 else 0.8)


def run_agent_benchmark(agent_name: str, agent, conversations: list[dict[str, Any]], config) -> BenchmarkRow:
    """Student TODO: evaluate one agent over many conversations.

    Pseudocode:
    1. Feed all turns to the agent.
    2. Track `agent tokens only`.
    3. Track `prompt tokens processed`.
    4. Ask recall questions in a fresh thread.
    5. Compute average recall and quality.
    6. Record memory file growth and compaction count.
    """

    users = {c['user_id'] for c in conversations}
    size = lambda: sum(agent.memory_file_size(u) for u in users) if hasattr(agent, 'memory_file_size') else 0
    before = size()
    threads, recall, quality = [], [], []
    for c in conversations:
        thread = 'conversation:' + c['id']
        threads.append(thread)
        for message in c['turns']:
            agent.reply(c['user_id'], thread, message)
        for index, question in enumerate(c['recall_questions']):
            fresh = f'recall:{c["id"]}:{index}'
            threads.append(fresh)
            answer = agent.reply(c['user_id'], fresh, question['question'])['answer']
            recall.append(recall_points(answer, question['expected_contains']))
            quality.append(heuristic_quality(answer, question['expected_contains']))
    return BenchmarkRow(agent_name, sum(agent.token_usage(t) for t in threads), sum(agent.prompt_token_usage(t) for t in threads), sum(recall) / len(recall) if recall else 0, sum(quality) / len(quality) if quality else 0, size() - before, sum(agent.compaction_count(t) for t in threads))


def format_rows(rows: list[BenchmarkRow]) -> str:
    """Student TODO: print a markdown table or tabulated output."""

    from tabulate import tabulate
    return tabulate([[r.agent_name, r.agent_tokens_only, r.prompt_tokens_processed, f'{r.recall_score:.1%}', f'{r.response_quality:.1%}', r.memory_growth_bytes, r.compactions] for r in rows], headers=['Agent', 'Agent tokens only', 'Prompt tokens processed', 'Cross-session recall', 'Response quality', 'Memory growth (bytes)', 'Compactions'], tablefmt='github')


def main() -> None:
    """Student TODO: run both benchmark suites.

    Required benchmark sections:
    - Standard benchmark from `data/conversations.json`
    - Long-context stress benchmark from `data/advanced_long_context.json`

    Compare:
    - Baseline
    - Advanced

    Keep the same output columns as the solved lab:
    - Agent tokens only
    - Prompt tokens processed
    - Cross-session recall
    - Response quality
    - Memory growth (bytes)
    - Compactions
    """

    config = load_config()
    for title, filename in [('Standard Benchmark', 'conversations.json'), ('Long-Context Stress Benchmark', 'advanced_long_context.json')]:
        data = load_conversations(config.data_dir / filename)
        with tempfile.TemporaryDirectory(prefix='memory-lab-') as directory:
            isolated = replace(config, state_dir=Path(directory))
            agents = [('Baseline', BaselineAgent(isolated, force_offline=True)), ('Advanced', AdvancedAgent(isolated, force_offline=True))]
            rows = [run_agent_benchmark(name, agent, data, isolated) for name, agent in agents]
            print('\n' + title + '\n' + format_rows(rows))
    print('\nOffline deterministic benchmark; tokens are estimates; quality is a recall/concision proxy. Training and recall turns are both included.')


if __name__ == "__main__":
    main()
