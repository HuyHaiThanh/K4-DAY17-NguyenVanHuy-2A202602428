"""Non-destructive decay of profile facts during retrieval."""
from __future__ import annotations
import json
import math
import time
from pathlib import Path
from typing import Callable
from memory_store import UserProfileStore


class DecayingProfile:
    def __init__(self, store: UserProfileStore, half_life_days: float = 30, minimum_priority: float = 0.25, clock: Callable[[], float] = time.time):
        if not math.isfinite(half_life_days) or half_life_days <= 0:
            raise ValueError('Memory half-life must be finite and positive')
        if not math.isfinite(minimum_priority) or not 0 < minimum_priority <= 1:
            raise ValueError('Memory minimum priority must be in (0, 1]')
        self.store = store
        self.half_life_days = half_life_days
        self.minimum_priority = minimum_priority
        self.clock = clock

    def metadata_path(self, user_id: str) -> Path:
        return self.store.path_for(user_id).with_name('memory_metadata.json')

    def metadata(self, user_id: str) -> dict:
        path = self.metadata_path(user_id)
        return json.loads(path.read_text(encoding='utf-8')) if path.exists() else {}

    def observe(self, user_id: str, updates: dict[str, str]) -> None:
        if not updates:
            return
        metadata = self.metadata(user_id)
        before = self.store.facts(user_id)
        now = int(self.clock())
        for key, value in updates.items():
            self.store.upsert_fact(user_id, key, value)
            final_value = self.store.facts(user_id)[key]
            previous = metadata.get(key, {})
            # Corrections reset reinforcement of the previous value.
            same_value = before.get(key) == final_value == previous.get('value')
            confirmations = previous.get('confirmations', 0) + 1 if same_value else 1
            metadata[key] = {'value': final_value, 'updated_at': now, 'confirmations': confirmations}
        path = self.metadata_path(user_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix('.tmp')
        temporary.write_text(json.dumps(metadata, ensure_ascii=False, sort_keys=True, separators=(',', ':')), encoding='utf-8')
        temporary.replace(path)

    def priorities(self, user_id: str) -> dict[str, float]:
        facts = self.store.facts(user_id)
        metadata = self.metadata(user_id)
        now = self.clock()
        priorities = {}
        for key, value in facts.items():
            entry = metadata.get(key)
            # Name is protected; legacy/manual facts have unknown age, not age zero.
            # Unknown age remains usable rather than inventing an expiration date.
            if key == 'name' or not entry or entry.get('value') != value:
                priorities[key] = 1.0
                continue
            age_days = max(0, now - entry['updated_at']) / 86400
            reinforcement = min(2.0, 1 + math.log2(max(1, entry['confirmations'])) / 4)
            priorities[key] = min(1.0, reinforcement * 2 ** (-age_days / self.half_life_days))
        return priorities

    def active_facts(self, user_id: str) -> dict[str, str]:
        priorities = self.priorities(user_id)
        return {key: value for key, value in self.store.facts(user_id).items() if priorities[key] >= self.minimum_priority}

    def context_text(self, user_id: str) -> str:
        if not self.store.read_text(user_id):
            return ''
        return '# User profile\n\n' + '\n'.join(f'- {key}: {json.dumps(value, ensure_ascii=False)}' for key, value in sorted(self.active_facts(user_id).items())) + '\n'

    def storage_size(self, user_id: str) -> int:
        path = self.metadata_path(user_id)
        return self.store.file_size(user_id) + (path.stat().st_size if path.exists() else 0)
