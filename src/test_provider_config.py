from dataclasses import replace
import sys
from types import SimpleNamespace
import pytest
from config import load_config
from model_provider import ProviderConfig, build_chat_model


@pytest.mark.parametrize('provider,module,class_name', [('openai','langchain_openai','ChatOpenAI'), ('custom','langchain_openai','ChatOpenAI'), ('openrouter','langchain_openai','ChatOpenAI'), ('gemini','langchain_google_genai','ChatGoogleGenerativeAI'), ('anthropic','langchain_anthropic','ChatAnthropic'), ('ollama','langchain_ollama','ChatOllama')])
def test_six_provider_factories_without_network(monkeypatch, provider, module, class_name):
    calls = []
    def constructor(**kwargs):
        calls.append(kwargs)
        return kwargs
    monkeypatch.setitem(sys.modules, module, SimpleNamespace(**{class_name: constructor}))
    config = ProviderConfig(provider, 'configured-model', 0, 'fake-key', 'http://localhost:1234/v1')
    build_chat_model(config)
    assert calls[0]['model'] == 'configured-model'
    if provider in ('openai', 'custom', 'openrouter', 'ollama'):
        assert calls[0]['base_url'] == config.base_url
    assert ('api_key' in calls[0]) == (provider != 'ollama')


def test_judge_provider_uses_its_own_default_and_credentials(tmp_path, monkeypatch):
    for key in ('JUDGE_MODEL', 'JUDGE_BASE_URL', 'JUDGE_TEMPERATURE'):
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setenv('LLM_PROVIDER', 'openai')
    monkeypatch.setenv('LLM_MODEL', 'main-openai-model')
    monkeypatch.setenv('JUDGE_PROVIDER', 'gemini')
    monkeypatch.setenv('JUDGE_API_KEY', 'judge-placeholder')
    config = load_config(tmp_path)
    assert config.judge_model.model_name != 'main-openai-model'
    assert config.judge_model.api_key == 'judge-placeholder'


def test_openrouter_uses_native_sdk_by_default(monkeypatch):
    monkeypatch.setitem(sys.modules, 'langchain_openrouter', SimpleNamespace(ChatOpenRouter=lambda **kwargs: kwargs))
    result = build_chat_model(ProviderConfig('openrouter', 'openai/example', 0, 'fake-key'))
    assert result == {'model': 'openai/example', 'temperature': 0, 'api_key': 'fake-key'}
