import hashlib
import json
from dataclasses import replace, fields
from pathlib import Path
from config import load_config
from agent_baseline import BaselineAgent
from agent_advanced import AdvancedAgent
from benchmark import BenchmarkRow, load_conversations, run_agent_benchmark, heuristic_quality
from benchmark_ablation import RecordingAgent, run_ablation


def test_same_input_order_and_one_fresh_recall_thread_per_conversation(tmp_path):
    config = replace(load_config(), state_dir=tmp_path)
    data = load_conversations(config.data_dir / 'conversations.json')
    recordings = []
    for cls in (BaselineAgent, AdvancedAgent):
        recorder = RecordingAgent(cls(config, True))
        run_agent_benchmark(cls.__name__, recorder, data, config)
        recordings.append([(r['user_id'], r['thread_id'], r['input_sha256']) for r in recorder.trace])
    assert recordings[0] == recordings[1]
    expected = []
    for c in data:
        expected.extend((c['user_id'], 'conversation:' + c['id'], hashlib.sha256(m.encode('utf-8')).hexdigest()) for m in c['turns'])
        expected.extend((c['user_id'], 'recall:' + c['id'], hashlib.sha256(q['question'].encode('utf-8')).hexdigest()) for q in c['recall_questions'])
        assert 'recall:' + c['id'] != 'conversation:' + c['id']
    assert recordings[0] == expected


def test_compact_ablation_attributes_prompt_savings(tmp_path):
    config = replace(load_config(), state_dir=tmp_path)
    original = config.compact_threshold_tokens
    rows, trace = run_ablation(config)
    baseline, enabled, disabled = rows
    assert config.compact_threshold_tokens == original
    assert enabled.compactions > 0
    assert disabled.compactions == 0
    assert enabled.prompt_tokens_processed < baseline.prompt_tokens_processed < disabled.prompt_tokens_processed
    assert enabled.recall_score == disabled.recall_score == 1
    assert enabled.agent_tokens_only == disabled.agent_tokens_only
    assert enabled.memory_growth_bytes == disabled.memory_growth_bytes
    turns = [r for r in trace['Baseline'] if r['thread_id'].startswith('conversation:')]
    assert turns[-1]['prompt_tokens'] > turns[0]['prompt_tokens']
    assert all(a['prompt_tokens'] < b['prompt_tokens'] for a, b in zip(turns, turns[1:]))


def test_benchmark_schema_keeps_original_column_names():
    assert [f.name for f in fields(BenchmarkRow)] == ['agent_name', 'agent_tokens_only', 'prompt_tokens_processed', 'recall_score', 'response_quality', 'memory_growth_bytes', 'compactions']
    assert heuristic_quality('Lan', ['Lan']) == 1


def test_offline_main_is_clean_and_reproducible_without_deleting_user_state(tmp_path, monkeypatch, capsys):
    import sys
    import benchmark
    config = replace(load_config(), state_dir=tmp_path / 'existing-state')
    config.state_dir.mkdir()
    sentinel = config.state_dir / 'User.md'
    sentinel.write_text('Existing personal profile', encoding='utf-8')
    monkeypatch.setattr(benchmark, 'load_config', lambda: config)
    monkeypatch.setenv('MEMORY_HALF_LIFE_DAYS', '0.000001')
    monkeypatch.setattr(sys, 'argv', ['benchmark.py'])
    benchmark.main()
    first = capsys.readouterr().out
    benchmark.main()
    second = capsys.readouterr().out
    assert first == second
    assert first.count('Standard Benchmark') == 1
    assert first.count('Long-Context Stress Benchmark') == 1
    assert first.count('| Baseline ') == 2
    assert first.count('| Advanced ') == 2
    assert '100.0%' in first
    assert sentinel.read_text(encoding='utf-8') == 'Existing personal profile'
    assert list(config.state_dir.iterdir()) == [sentinel]


def test_original_datasets_are_unchanged():
    # Normalize Windows checkout line endings; content must match original input.
    expected = {"conversations.json":"13f6569675500babce3d4a7fc4f5b2c2bea65af12be7d96d2a04d21b7d0a803c","advanced_long_context.json":"8532a0f68298dc3d070210864f0a776bc51df0b5b19766944f1651643a914f8d"}
    root = Path(__file__).resolve().parent.parent
    for filename, sha256 in expected.items():
        content = (root / "data" / filename).read_text(encoding="utf-8")
        assert hashlib.sha256(content.encode("utf-8")).hexdigest() == sha256
