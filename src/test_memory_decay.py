from dataclasses import replace
import pytest
from agent_advanced import AdvancedAgent
from config import load_config
from memory_decay import DecayingProfile
from memory_store import UserProfileStore

DAY = 86400


def test_decay_reduces_context_without_deleting_profile(tmp_path):
    store = UserProfileStore(tmp_path)
    current = [0]
    profile = DecayingProfile(store, 30, 0.25, clock=lambda: current[0])
    profile.observe('u', {'name': 'Lan', 'location': 'Huế'})
    before = profile.context_text('u')
    current[0] = 30 * DAY
    assert profile.priorities('u')['location'] == 0.5
    current[0] = 90 * DAY
    assert profile.active_facts('u') == {'name': 'Lan'}
    assert len(profile.context_text('u')) < len(before)
    assert store.facts('u')['location'] == 'Huế'
    assert profile.storage_size('u') > store.file_size('u')


def test_reconfirmation_and_correction(tmp_path):
    current = [0]
    profile = DecayingProfile(UserProfileStore(tmp_path), clock=lambda: current[0])
    profile.observe('u', {'location': 'Huế'})
    current[0] = 90 * DAY
    assert 'location' not in profile.active_facts('u')
    profile.observe('u', {'location': 'Huế'})
    assert profile.metadata('u')['location']['confirmations'] == 2
    assert profile.active_facts('u')['location'] == 'Huế'
    profile.observe('u', {'location': 'Đà Nẵng'})
    assert profile.metadata('u')['location']['confirmations'] == 1
    assert profile.active_facts('u')['location'] == 'Đà Nẵng'


def test_reinforcement_extends_priority_and_survives_restart(tmp_path):
    store = UserProfileStore(tmp_path)
    profile = DecayingProfile(store, clock=lambda: 0)
    for _ in range(16):
        profile.observe('u', {'location': 'Huế'})
    restarted = DecayingProfile(store, clock=lambda: 90 * DAY)
    assert restarted.priorities('u')['location'] == 0.25
    assert restarted.active_facts('u')['location'] == 'Huế'
    assert 'location' not in DecayingProfile(store, clock=lambda: 91 * DAY).active_facts('u')


def test_legacy_manual_profiles_are_not_silently_expired(tmp_path):
    store = UserProfileStore(tmp_path)
    store.write_text('u', '# User\n- location: Huế\n')
    profile = DecayingProfile(store, clock=lambda: 999 * DAY)
    assert profile.active_facts('u')['location'] == 'Huế'
    profile.observe('u', {'location': 'Huế'})
    store.write_text('u', '# User\n- location: Đà Nẵng\n')
    assert profile.active_facts('u')['location'] == 'Đà Nẵng'


def test_agent_decay_changes_prompt_and_recall_after_restart(tmp_path):
    config = replace(load_config(), state_dir=tmp_path)
    agent = AdvancedAgent(config, True)
    agent.decaying_profile.clock = lambda: 0
    agent.reply('u', 't', 'Mình tên là Lan. Mình đang ở Huế.')
    restarted = AdvancedAgent(config, True)
    restarted.decaying_profile.clock = lambda: 90 * DAY
    query = 'Mình đang ở đâu?'
    before = agent.reply('u', 'q', query)
    after = restarted.reply('u', 'q', query)
    assert 'Huế' in before['answer']
    assert 'Huế' not in after['answer']
    assert after['prompt_tokens'] < before['prompt_tokens']
    assert restarted.profile_store.facts('u')['location'] == 'Huế'
    metadata_before = restarted.decaying_profile.metadata('u')
    restarted.reply('u', 'q', 'Có lẽ mình đang ở Hà Nội.')
    assert restarted.decaying_profile.metadata('u') == metadata_before
    restarted.reply('u', 'new', 'Mình đang ở Đà Nẵng.')
    assert 'Đà Nẵng' in restarted.reply('u', 'new-q', query)['answer']


@pytest.mark.parametrize('half_life,priority', [(0, 0.25), (-1, 0.25), (float('inf'), 0.25), (30, 0), (30, 1.1), (30, float('nan'))])
def test_invalid_decay_settings(tmp_path, half_life, priority):
    with pytest.raises(ValueError):
        DecayingProfile(UserProfileStore(tmp_path), half_life, priority)
