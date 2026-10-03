from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ProviderConfig:
    """Student TODO: define the provider configuration shared by the agents.

    Required providers for this lab:
    - openai
    - custom (OpenAI-compatible base URL)
    - gemini
    - anthropic
    - ollama
    - openrouter
    """

    provider: str
    model_name: str
    temperature: float
    api_key: str | None = None
    base_url: str | None = None


def normalize_provider(value: str) -> str:
    """Student TODO: map aliases like `anthorpic` -> `anthropic`."""

    value = value.strip().lower()
    value = {'anthorpic': 'anthropic', 'google': 'gemini', 'openai-compatible': 'custom'}.get(value, value)
    if value not in {'openai', 'custom', 'gemini', 'anthropic', 'ollama', 'openrouter'}:
        raise ValueError(f'Unsupported provider: {value}')
    return value


def build_chat_model(config: ProviderConfig):
    """Student TODO: instantiate the real chat model for the selected provider.

    Pseudocode:
    - `openai` -> `ChatOpenAI`
    - `custom` -> `ChatOpenAI` with `base_url`
    - `gemini` -> `ChatGoogleGenerativeAI`
    - `anthropic` -> `ChatAnthropic`
    - `ollama` -> `ChatOllama`
    - `openrouter` -> `ChatOpenRouter`
    """

    provider = normalize_provider(config.provider)
    kwargs = {'model': config.model_name, 'temperature': config.temperature}
    if config.api_key:
        kwargs['api_key'] = config.api_key
    if provider == 'openrouter' and not config.base_url:
        from langchain_openrouter import ChatOpenRouter
        return ChatOpenRouter(**kwargs)
    if provider in {'openai', 'custom', 'openrouter'}:
        from langchain_openai import ChatOpenAI
        if provider == 'custom' and not config.base_url:
            raise ValueError('custom provider requires base_url')
        if config.base_url or provider == 'openrouter':
            kwargs['base_url'] = config.base_url or 'https://openrouter.ai/api/v1'
        return ChatOpenAI(**kwargs)
    if provider == 'gemini':
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(**kwargs)
    if provider == 'anthropic':
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(**kwargs)
    from langchain_ollama import ChatOllama
    kwargs.pop('api_key', None)
    if config.base_url:
        kwargs['base_url'] = config.base_url
    return ChatOllama(**kwargs)
