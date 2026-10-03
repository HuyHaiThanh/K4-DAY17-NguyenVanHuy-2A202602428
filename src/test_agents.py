from dataclasses import replace
from pathlib import Path
import pytest
from config import load_config
from memory_store import UserProfileStore, CompactMemoryManager, extract_profile_updates, estimate_tokens
from agent_baseline import BaselineAgent
from agent_advanced import AdvancedAgent
from benchmark import load_conversations, run_agent_benchmark, recall_points


def make_config(tmp_path: Path):
    return replace(load_config(), state_dir=tmp_path, compact_threshold_tokens=150, compact_keep_messages=2)


def test_user_markdown_read_write_edit(tmp_path):
    s = UserProfileStore(tmp_path)
    assert s.read_text('u') == ''
    s.write_text('u', 'Tên: Lan')
    assert s.read_text('u') == 'Tên: Lan'
    assert s.edit_text('u', 'Lan', 'Mai')
    assert not s.edit_text('u', 'missing', 'x')
    assert s.file_size('u') == len('Tên: Mai'.encode())
    s.upsert_fact('v', 'location', 'Huế')
    s.upsert_fact('v', 'location', 'Đà Nẵng')
    assert s.facts('v') == {'location': 'Đà Nẵng'}
    assert s.path_for('../u').is_relative_to(tmp_path)
    assert s.path_for('../u') != s.path_for('u')


def test_compact_trigger(tmp_path):
    m = CompactMemoryManager(100, 2)
    for i in range(12):
        m.append('t', 'user', f'{i}: ' + 'context ' * 80)
    c = m.context('t')
    assert c['compactions'] > 1
    assert len(c['messages']) == 2
    assert c['messages'][-1]['content'].startswith('11:')
    assert 0 < len(c['summary']) <= 100 * 4 // 3
    assert m.compaction_count('other') == 0


def test_cross_session_recall(tmp_path):
    c = make_config(tmp_path)
    for cls in (BaselineAgent, AdvancedAgent):
        agent = cls(c, True)
        agent.reply('u', 'old', 'Mình tên là Lan.')
        assert 'Lan' in agent.reply('u', 'old', 'Mình tên gì?')['answer']
        result = agent.reply('u', 'new', 'Mình tên gì?')['answer']
        assert ('Lan' in result) == (cls is AdvancedAgent)
    restarted = AdvancedAgent(c, True)
    assert 'Lan' in restarted.reply('u', 'restart', 'Mình tên gì?')['answer']
    assert 'Lan' not in restarted.reply('v', 'other', 'Mình tên gì?')['answer']
    with pytest.raises(ValueError):
        restarted.reply('v', 'restart', 'hello')


def test_compact_reduces_prompt_load_on_long_thread(tmp_path):
    c = make_config(tmp_path)
    b, a = BaselineAgent(c, True), AdvancedAgent(c, True)
    for _ in range(20):
        for agent in (b, a):
            agent.reply('u', 't', 'Nội dung thảo luận tạm thời. ' * 100)
    assert a.compaction_count('t') > 0
    assert a.prompt_token_usage('t') < b.prompt_token_usage('t')


def test_noise_and_corrections(tmp_path):
    a = AdvancedAgent(make_config(tmp_path), True)
    messages = ['Mình ở Đà Nẵng và đang làm backend engineer.', 'À, mình đính chính: giờ mình đang ở Huế chứ không còn ở Đà Nẵng.', 'Mình không còn làm backend engineer nữa, giờ chuyển sang MLOps engineer.', 'Hà Nội chỉ là nơi mình ra họp, không phải nơi ở hiện tại.', 'Mình đùa là chuyển sang product manager, nhưng đó chỉ là câu đùa.']
    for message in messages:
        a.reply('u', 't', message)
    facts = a.profile_store.facts('u')
    assert facts['location'] == 'Huế'
    assert facts['profession'] == 'MLOps engineer'
    assert extract_profile_updates('Bạn có biết DũngCT không?') == {}
    before = a.profile_store.read_text('u')
    a.reply('u', 'recall', 'Nếu ai đó nhắc Huế, Hà Nội hay product manager, nghề hiện tại là gì?')
    assert a.profile_store.read_text('u') == before


def test_dataset_benchmarks(tmp_path):
    c = make_config(tmp_path)
    for filename in ('conversations.json', 'advanced_long_context.json'):
        data = load_conversations(c.data_dir / filename)
        a = AdvancedAgent(replace(c, state_dir=tmp_path / filename), True)
        b = BaselineAgent(c, True)
        ar = run_agent_benchmark('Advanced', a, data, c)
        br = run_agent_benchmark('Baseline', b, data, c)
        assert ar.recall_score == 1.0
        assert br.recall_score < ar.recall_score
        assert ar.compactions > 0
        assert ar.memory_growth_bytes > 0
        assert br.memory_growth_bytes == 0
        if filename.startswith('advanced'):
            assert ar.prompt_tokens_processed < br.prompt_tokens_processed


def test_token_and_recall_conventions():
    assert estimate_tokens('   ') == 0
    assert estimate_tokens('abcde') == 2
    assert recall_points('Python', ['Python', 'AI']) == 0.5
    assert recall_points('python AI', ['Python', 'AI']) == 1
