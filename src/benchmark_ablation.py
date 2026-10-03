"""Measure compact enabled/disabled without editing data or persisted config."""
from dataclasses import asdict, replace
from pathlib import Path
import tempfile
import json
import hashlib
from config import load_config
from agent_baseline import BaselineAgent
from agent_advanced import AdvancedAgent
from benchmark import load_conversations, run_agent_benchmark, format_rows


class RecordingAgent:
    def __init__(self, agent):
        self.agent = agent
        self.trace = []

    def __getattr__(self, name):
        return getattr(self.agent, name)

    def reply(self, user_id, thread_id, message):
        result = self.agent.reply(user_id, thread_id, message)
        self.trace.append({'user_id': user_id, 'thread_id': thread_id,
                           'input_sha256': hashlib.sha256(message.encode('utf-8')).hexdigest(),
                           'prompt_tokens': result['prompt_tokens'],
                           'agent_tokens': result['agent_tokens']})
        return result


def run_ablation(config):
    data = load_conversations(config.data_dir / 'advanced_long_context.json')
    with tempfile.TemporaryDirectory(prefix='compact-ablation-') as directory:
        rows, traces = [], {}
        for name, cls, threshold in [('Baseline', BaselineAgent, config.compact_threshold_tokens),
                                      ('Advanced compact ON', AdvancedAgent, config.compact_threshold_tokens),
                                      ('Advanced compact OFF', AdvancedAgent, 10 ** 12)]:
            isolated = replace(config, state_dir=Path(directory) / name, compact_threshold_tokens=threshold)
            agent = cls(isolated, force_offline=True)
            if hasattr(agent, 'decaying_profile'):
                agent.decaying_profile.clock = lambda: 1700000000
            recorder = RecordingAgent(agent)
            rows.append(run_agent_benchmark(name, recorder, data, isolated))
            traces[name] = recorder.trace
        return rows, traces


def main():
    config = load_config()
    rows, traces = run_ablation(config)
    print('Compact ablation — original stress input, clean isolated state, fixed offline clock')
    print(format_rows(rows))
    print('Original compact threshold is unchanged:', config.compact_threshold_tokens)
    print('Per-turn trace (JSON):')
    print(json.dumps(traces, ensure_ascii=False, sort_keys=True, indent=2))


if __name__ == '__main__':
    main()
