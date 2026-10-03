import pytest
from types import SimpleNamespace
from quality_judge import QualityJudge


class FakeJudge:
    def __init__(self, content):
        self.content = content
    def invoke(self, messages):
        assert 'expected_facts' in messages[1][1]
        return SimpleNamespace(content=self.content)


def test_semantic_judge_score():
    judge = QualityJudge(FakeJudge('{"score": 0.75}'))
    assert judge.score('Tên gì?', 'Lan', ['Lan']) == 0.75
    assert judge.calls == 1


@pytest.mark.parametrize('content', ['{"score": 1.5}', '{"score": -1}', '{"score": true}', '{"score": "1"}', '{"score": NaN}'])
def test_invalid_judge_scores(content):
    with pytest.raises(ValueError):
        QualityJudge(FakeJudge(content)).score('q', 'a', ['x'])


def test_benchmark_uses_semantic_judge_when_attached(tmp_path):
    from dataclasses import replace
    from config import load_config
    from agent_baseline import BaselineAgent
    from benchmark import run_agent_benchmark
    config = replace(load_config(), state_dir=tmp_path)
    agent = BaselineAgent(config, True)
    agent.quality_judge = QualityJudge(FakeJudge('{"score": 0.75}'))
    dataset = [{'id': 'one', 'user_id': 'u', 'turns': ['Mình tên là Lan.'], 'recall_questions': [{'question': 'Mình tên gì?', 'expected_contains': ['Lan']}]}]
    result = run_agent_benchmark('Baseline', agent, dataset, config)
    assert result.response_quality == 0.75
    assert agent.quality_judge.calls == 1
