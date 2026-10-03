"""Deterministic time-travel demonstration of persistent memory decay."""
from pathlib import Path
import tempfile
from memory_store import UserProfileStore, estimate_tokens
from memory_decay import DecayingProfile


def main():
    with tempfile.TemporaryDirectory(prefix='decay-lab-') as directory:
        current = [0]
        profile = DecayingProfile(UserProfileStore(Path(directory)), clock=lambda: current[0])
        profile.observe('u', {'name': 'Lan', 'location': 'Huế', 'profession': 'MLOps engineer'})
        print('| Scenario | Location priority | Active fields | Profile context tokens |')
        print('|---|---:|---|---:|')
        def row(label):
            print(f'| {label} | {profile.priorities("u")["location"]:.3f} | {", ".join(sorted(profile.active_facts("u")))} | {estimate_tokens(profile.context_text("u"))} |')
        row('Day 0')
        current[0] = 90 * 86400
        row('Day 90 without confirmation')
        profile.observe('u', {'location': 'Huế'})
        row('Day 90 after reconfirmation')
        print('Raw profile retains all facts. Name is protected. Decay affects retrieval, not physical deletion.')


if __name__ == '__main__':
    main()
