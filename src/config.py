from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from model_provider import ProviderConfig

import os
from model_provider import ProviderConfig, normalize_provider


@dataclass
class LabConfig:
    """Student TODO: define the shared configuration for the lab.

    Hints:
    - Keep paths for the repo root, dataset directory, and state directory.
    - Add compact-memory settings such as threshold and number of messages to keep.
    - Add provider settings for `openai`, `custom`, `gemini`, `anthropic`, `ollama`, and `openrouter`.
    """

    base_dir: Path
    data_dir: Path
    state_dir: Path
    compact_threshold_tokens: int
    compact_keep_messages: int
    model: ProviderConfig
    judge_model: ProviderConfig


def load_config(base_dir: Path | None = None) -> LabConfig:
    """Student TODO: load environment variables and return a LabConfig.

    Pseudocode:
    1. Resolve the repo root or default to the current file parent.
    2. Optionally load values from `.env`.
    3. Create `state/` if it does not exist.
    4. Return a populated LabConfig instance.
    """

    root = (base_dir or Path(__file__).resolve().parent.parent).resolve()
    from dotenv import load_dotenv
    load_dotenv(root / '.env', override=False)
    def provider_config(prefix):
        provider = normalize_provider(os.getenv(prefix + 'PROVIDER', os.getenv('LLM_PROVIDER', 'openai')))
        keys = {'openai': 'OPENAI', 'custom': 'CUSTOM', 'gemini': 'GEMINI', 'anthropic': 'ANTHROPIC', 'ollama': 'OLLAMA', 'openrouter': 'OPENROUTER'}
        defaults = {'openai': 'gpt-4o-mini', 'custom': 'local-model', 'gemini': 'gemini-2.5-flash', 'anthropic': 'claude-sonnet-4-5', 'ollama': 'llama3.2', 'openrouter': 'openai/gpt-4o-mini'}
        key = keys[provider]
        return ProviderConfig(provider, os.getenv(prefix + 'MODEL', os.getenv('LLM_MODEL', defaults[provider])), float(os.getenv(prefix + 'TEMPERATURE', '0')), os.getenv(key + '_API_KEY'), os.getenv(key + '_BASE_URL'))
    threshold = int(os.getenv('COMPACT_THRESHOLD_TOKENS', '1000'))
    keep = int(os.getenv('COMPACT_KEEP_MESSAGES', '4'))
    if threshold <= 0 or keep < 1:
        raise ValueError('Compact threshold must be positive and keep_messages >= 1')
    state = root / 'state'
    state.mkdir(parents=True, exist_ok=True)
    return LabConfig(root, root / 'data', state, threshold, keep, provider_config('LLM_'), provider_config('JUDGE_'))
