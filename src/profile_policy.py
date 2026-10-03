"""Rule-based confidence gate; scores are policy weights, not probabilities."""
from dataclasses import dataclass
import math
import re
from memory_store import extract_profile_updates


@dataclass(frozen=True)
class ProfileDecision:
    key: str
    value: str
    confidence: float
    reason: str
    accepted: bool


class ProfileMemoryPolicy:
    def __init__(self, threshold: float = 0.8):
        if not math.isfinite(threshold) or not 0 <= threshold <= 1:
            raise ValueError('Profile confidence threshold must be between 0 and 1')
        self.threshold = threshold

    def evaluate(self, message: str) -> list[ProfileDecision]:
        decisions = []
        # Scope evidence to each sentence so a later question does not suppress
        # an earlier independent assertion. Mixed ambiguous sentences are conservative.
        for sentence in re.split(r'(?<=[.!?])\s+|\n+', message.strip()):
            low = sentence.casefold()
            candidates = extract_profile_updates(sentence)
            if not candidates:
                continue
            if '?' in sentence or re.search(r'\b(?:có phải|phải không|đúng không|tên gì|là gì|ở đâu|nghề gì)\b', low):
                score, reason = 0.0, 'question'
            elif any(term in low for term in ('giả sử', 'giả dụ', 'nếu ', 'đùa', 'người khác', 'bạn mình', 'đồng nghiệp nói')) or low.startswith('ví dụ:'):
                score, reason = 0.1, 'hypothetical_or_third_party'
            elif any(term in low for term in ('có lẽ', 'có thể', 'chắc là', 'hình như', 'chưa chắc', 'không chắc', 'dự định', 'định chuyển', 'sẽ chuyển')):
                score, reason = 0.4, 'uncertain_or_future'
            else:
                score, reason = 0.95, 'assertion'
            decisions.extend(ProfileDecision(key, value, score, reason, score > 0 and score >= self.threshold) for key, value in candidates.items())
        return decisions

    def accepted_updates(self, message: str) -> dict[str, str]:
        updates = {}
        for decision in self.evaluate(message):
            if decision.accepted:
                if decision.key == 'interests' and decision.key in updates:
                    updates[decision.key] = ', '.join(dict.fromkeys(updates[decision.key].split(', ') + decision.value.split(', ')))
                else:
                    updates[decision.key] = decision.value
        return updates
