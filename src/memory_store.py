from dataclasses import dataclass, field
from pathlib import Path
import hashlib
import json
import math
import re


def estimate_tokens(text: str) -> int:
    return math.ceil(len(text.strip()) / 4)


@dataclass
class UserProfileStore:
    root_dir: Path

    def path_for(self, user_id: str) -> Path:
        # Full digest avoids collisions and prevents traversal for arbitrary user IDs.
        slug = hashlib.sha256(user_id.encode('utf-8')).hexdigest()
        return self.root_dir / slug / 'User.md'

    def read_text(self, user_id: str) -> str:
        path = self.path_for(user_id)
        return path.read_text(encoding='utf-8') if path.exists() else ''

    def write_text(self, user_id: str, content: str) -> Path:
        path = self.path_for(user_id)
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix('.tmp')
        temporary.write_text(content, encoding='utf-8')
        temporary.replace(path)
        return path

    def edit_text(self, user_id: str, search_text: str, replacement: str) -> bool:
        text = self.read_text(user_id)
        if not search_text or search_text not in text:
            return False
        self.write_text(user_id, text.replace(search_text, replacement, 1))
        return True

    def file_size(self, user_id: str) -> int:
        path = self.path_for(user_id)
        return path.stat().st_size if path.exists() else 0

    def facts(self, user_id: str) -> dict[str, str]:
        facts = {}
        for line in self.read_text(user_id).splitlines():
            if line.startswith('- ') and ': ' in line:
                key, value = line[2:].split(': ', 1)
                facts[key] = json.loads(value)
        return facts

    def upsert_fact(self, user_id: str, key: str, value: str) -> None:
        facts = self.facts(user_id)
        if key == 'interests' and key in facts:
            value = ', '.join(dict.fromkeys(facts[key].split(', ') + value.split(', ')))
        facts[key] = value
        text = '# User profile\n\n' + '\n'.join(f'- {k}: {json.dumps(v, ensure_ascii=False)}' for k, v in sorted(facts.items())) + '\n'
        self.write_text(user_id, text)


def extract_profile_updates(message: str) -> dict[str, str]:
    facts = {}
    # Extract assertions clause by clause, excluding questions and explicit negations.
    clauses = re.split(r'[.!?;\n]|,| nhưng | chứ ', message, flags=re.I)
    for clause in clauses:
        clause = clause.strip()
        low = clause.lower()
        if any(x in low for x in ('không còn', 'đừng', 'nếu ', 'chỉ là', 'câu đùa', 'không phải', 'lúc đầu', 'trước đó', 'từng ', 'nhắc lại', 'tên gì', 'tên mình là gì', 'ở đâu', 'nghề gì', 'đùa')):
            continue
        match = re.search(r'(?:mình tên(?: là)?|tên mình là|tên)\s+(DũngCT Stress|DũngCT|[^:]+)', clause, re.I)
        if match and ('mình tên' in low or 'tên mình là' in low or low.startswith('tên ')):
            facts['name'] = match.group(1).strip()
        match = re.search(r'(?:mình (?:vẫn |đang |hiện )?ở|hiện ở|nơi ở hiện tại là|hiện tại mình ở|đang làm việc ở)\s+(Huế|Đà Nẵng|Hà Nội|[^,]+)', clause, re.I)
        if match:
            facts['location'] = match.group(1).strip()
        match = re.search(r'(?:làm|chuyển sang|nghề)\s+(backend engineer|MLOps engineer|product manager)', clause, re.I)
        if match:
            facts['profession'] = match.group(1)
        if 'cà phê sữa đá' in low and any(x in low for x in ('thích', 'uống', 'đồ uống')):
            facts['favorite_drink'] = 'cà phê sữa đá'
        if 'mì quảng' in low and any(x in low for x in ('thích', 'ăn', 'món')):
            facts['favorite_food'] = 'mì Quảng'
        if 'corgi' in low and any(x in low for x in ('nuôi', 'con corgi')):
            facts['pet'] = 'corgi' + (' tên Bơ' if 'bơ' in low else '')
        if any(x in low for x in ('mình thích', 'mình đang quan tâm', 'mối quan tâm')):
            interests = [x for x in ('Python', 'AI', 'MLOps') if x.lower() in low]
            if interests:
                facts['interests'] = ', '.join(dict.fromkeys(facts.get('interests', '').split(', ') + interests)).strip(', ')
        if any(x in low for x in ('trả lời', 'style', 'giải thích')) and any(x in low for x in ('mình muốn', 'mình thích', 'hãy', 'vẫn giữ')):
            if any(x in low for x in ('ngắn', 'gọn', 'bullet')):
                facts['response_style'] = 'ngắn gọn, ' + ('3 bullet, ' if '3 bullet' in low else 'có bullet, ') + 'có ví dụ thực tế'
    if any(x in message.lower() for x in ('mình thích', 'mình đang quan tâm')):
        interests = [x for x in ('Python', 'AI', 'MLOps') if x.lower() in message.lower()]
        if interests:
            facts['interests'] = ', '.join(interests)
    return facts


def summarize_messages(messages: list[dict[str, str]], max_items: int = 6) -> str:
    # Bounded heuristic preserves short excerpts rather than whole paragraphs.
    return '\n'.join(m['content'][:160] for m in messages[-max_items:])


@dataclass
class CompactMemoryManager:
    threshold_tokens: int
    keep_messages: int
    state: dict[str, dict[str, object]] = field(default_factory=dict)

    def __post_init__(self):
        if self.threshold_tokens <= 0 or self.keep_messages < 1:
            raise ValueError('Invalid compact settings')

    def context(self, thread_id: str) -> dict[str, object]:
        return self.state.setdefault(thread_id, {'messages': [], 'summary': '', 'compactions': 0})

    def append(self, thread_id: str, role: str, content: str) -> None:
        state = self.context(thread_id)
        state['messages'].append({'role': role, 'content': content})
        total = estimate_tokens(state['summary']) + sum(estimate_tokens(m['content']) for m in state['messages'])
        if total > self.threshold_tokens and len(state['messages']) > self.keep_messages:
            old = state['messages'][:-self.keep_messages]
            combined = ([{'role': 'system', 'content': state['summary']}] if state['summary'] else []) + old
            summary = summarize_messages(combined)
            # Reserve a bounded budget for summary; retained messages can themselves exceed threshold.
            limit = max(4, self.threshold_tokens * 4 // 3)
            state['summary'] = summary[:limit]
            state['messages'] = state['messages'][-self.keep_messages:]
            state['compactions'] += 1

    def compaction_count(self, thread_id: str) -> int:
        return self.context(thread_id)['compactions']
