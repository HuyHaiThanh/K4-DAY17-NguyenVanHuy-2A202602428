from dataclasses import replace
import pytest
from agent_advanced import AdvancedAgent
from config import load_config
from profile_policy import ProfileMemoryPolicy


@pytest.mark.parametrize('message', ['Có lẽ mình đang ở Hà Nội.', 'Mình đang ở Hà Nội phải không?', 'Giả sử mình đang ở Hà Nội.', 'Bạn mình nói mình đang ở Hà Nội.'])
def test_uncertain_facts_never_overwrite_persistent_profile(tmp_path, message):
    config = replace(load_config(), state_dir=tmp_path)
    agent = AdvancedAgent(config, force_offline=True)
    agent.reply('u', 't', 'Mình đang ở Huế.')
    before = agent.profile_store.read_text('u')
    agent.reply('u', 't', message)
    assert agent.profile_store.read_text('u') == before
    assert agent.last_profile_decisions
    assert all(not decision.accepted for decision in agent.last_profile_decisions)
    restarted = AdvancedAgent(config, force_offline=True)
    assert 'Huế' in restarted.reply('u', 'new', 'Mình đang ở đâu?')['answer']
    assert 'Hà Nội' not in restarted.reply('u', 'new', 'Mình đang ở đâu?')['answer']


def test_threshold_controls_admission_and_boundary():
    message = 'Có lẽ mình đang ở Hà Nội.'
    assert ProfileMemoryPolicy(0.8).accepted_updates(message) == {}
    assert ProfileMemoryPolicy(0.4).accepted_updates(message)['location'] == 'Hà Nội'
    assert ProfileMemoryPolicy(0.95).accepted_updates('Mình đang ở Huế.')['location'] == 'Huế'
    assert ProfileMemoryPolicy(0.96).accepted_updates('Mình đang ở Huế.') == {}


def test_assertion_and_followup_question_are_scoped_separately():
    policy = ProfileMemoryPolicy()
    assert policy.accepted_updates('Mình tên là Lan. Mình đang ở Hà Nội phải không?') == {'name': 'Lan'}


def test_clear_correction_is_persisted(tmp_path):
    agent = AdvancedAgent(replace(load_config(), state_dir=tmp_path), True)
    agent.reply('u', 't', 'Mình đang ở Huế và đang làm backend engineer.')
    agent.reply('u', 't', 'Mình đính chính: giờ mình đang ở Đà Nẵng. Giờ chuyển sang MLOps engineer.')
    facts = agent.profile_store.facts('u')
    assert facts['location'] == 'Đà Nẵng'
    assert facts['profession'] == 'MLOps engineer'
    assert 'Huế' not in agent.profile_store.read_text('u')


@pytest.mark.parametrize('threshold', [-0.1, 1.1, float('nan'), float('inf')])
def test_invalid_threshold(threshold):
    with pytest.raises(ValueError):
        ProfileMemoryPolicy(threshold)


def test_agent_reads_threshold_environment(tmp_path, monkeypatch):
    monkeypatch.setenv('PROFILE_CONFIDENCE_THRESHOLD', '0.96')
    agent = AdvancedAgent(replace(load_config(), state_dir=tmp_path), True)
    agent.reply('u', 't', 'Mình tên là Lan.')
    assert agent.profile_store.facts('u') == {}
    assert agent.memory_file_size('u') == 0


def test_questions_rejected_even_when_threshold_is_zero():
    assert ProfileMemoryPolicy(0).accepted_updates('Mình đang ở Hà Nội phải không?') == {}


def test_style_example_is_not_a_hypothetical_fact():
    updates = ProfileMemoryPolicy().accepted_updates('Mình muốn bạn trả lời ngắn gọn, rõ ý và có ví dụ thực tế.')
    assert 'ngắn gọn' in updates['response_style']


def test_gate_reduces_pollution_against_permissive_policy(tmp_path, monkeypatch):
    configs = [replace(load_config(), state_dir=tmp_path / name) for name in ('strict', 'permissive')]
    monkeypatch.setenv('PROFILE_CONFIDENCE_THRESHOLD', '0.8')
    strict = AdvancedAgent(configs[0], True)
    monkeypatch.setenv('PROFILE_CONFIDENCE_THRESHOLD', '0.4')
    permissive = AdvancedAgent(configs[1], True)
    for agent in (strict, permissive):
        agent.reply('u', 't', 'Mình đang ở Huế.')
        agent.reply('u', 't', 'Có lẽ mình đang ở Hà Nội.')
    assert strict.profile_store.facts('u')['location'] == 'Huế'
    assert permissive.profile_store.facts('u')['location'] == 'Hà Nội'
