from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from config import LabConfig, load_config
from memory_store import CompactMemoryManager, UserProfileStore, estimate_tokens, extract_profile_updates
from model_provider import build_chat_model

from offline_response import answer_from_facts
from profile_policy import ProfileMemoryPolicy
import os


@dataclass
class AgentContext:
    user_id: str
    memory_path: str


class AdvancedAgent:
    """Student TODO: implement Agent B / Advanced Agent.

    Required memory layers:
    1. within-session memory
    2. persistent `User.md`
    3. compact memory for long threads
    """

    def __init__(self, config: LabConfig | None = None, force_offline: bool = False) -> None:
        self.config = config or load_config()
        self.force_offline = force_offline
        self.profile_policy = ProfileMemoryPolicy(float(os.getenv("PROFILE_CONFIDENCE_THRESHOLD", "0.8")))
        self.last_profile_decisions = []
        self.profile_store = UserProfileStore(self.config.state_dir / 'profiles')
        self.compact_memory = CompactMemoryManager(self.config.compact_threshold_tokens, self.config.compact_keep_messages)
        self.thread_tokens: dict[str, int] = {}
        self.thread_prompt_tokens: dict[str, int] = {}
        self.owners = {}
        self.langchain_agent = None if force_offline else self._maybe_build_langchain_agent()

    def reply(self, user_id: str, thread_id: str, message: str) -> dict[str, Any]:
        """Student TODO: route between offline mode and live mode."""

        if thread_id in self.owners and self.owners[thread_id] != user_id:
            raise ValueError('Thread belongs to another user')
        self.owners[thread_id] = user_id
        return self._reply_offline(user_id, thread_id, message)

    def token_usage(self, thread_id: str) -> int:
        return self.thread_tokens.get(thread_id, 0)

    def prompt_token_usage(self, thread_id: str) -> int:
        return self.thread_prompt_tokens.get(thread_id, 0)

    def memory_file_size(self, user_id: str) -> int:
        return self.profile_store.file_size(user_id)

    def compaction_count(self, thread_id: str) -> int:
        return self.compact_memory.compaction_count(thread_id)

    def _reply_offline(self, user_id: str, thread_id: str, message: str) -> dict[str, Any]:
        """Student TODO: implement the deterministic advanced path.

        Pseudocode:
        1. Extract stable profile facts from the incoming message.
        2. Persist those facts into `User.md`.
        3. Append the message into compact memory.
        4. Estimate prompt-context load from `User.md` + summary + recent messages.
        5. Generate a response that can answer long-term recall questions.
        6. Append the assistant reply and update token counters.
        """

        self.last_profile_decisions = self.profile_policy.evaluate(message)
        for key, value in self.profile_policy.accepted_updates(message).items():
            self.profile_store.upsert_fact(user_id, key, value)
        self.compact_memory.append(thread_id, 'user', message)
        prompt_tokens = self._estimate_prompt_context_tokens(user_id, thread_id)
        if self.langchain_agent is None:
            answer = self._offline_response(user_id, thread_id, message)
        else:
            context = self.compact_memory.context(thread_id)
            prompt = [('system', self.profile_store.read_text(user_id) + '\n' + context['summary'])]
            prompt.extend((m['role'], m['content']) for m in context['messages'])
            result = self.langchain_agent.invoke(prompt)
            answer = result.content if isinstance(result.content, str) else str(result.content)
        self.compact_memory.append(thread_id, 'assistant', answer)
        tokens = estimate_tokens(answer)
        self.thread_tokens[thread_id] = self.token_usage(thread_id) + tokens
        self.thread_prompt_tokens[thread_id] = self.prompt_token_usage(thread_id) + prompt_tokens
        return {'answer': answer, 'agent_tokens': tokens, 'prompt_tokens': prompt_tokens}

    def _estimate_prompt_context_tokens(self, user_id: str, thread_id: str) -> int:
        """Student TODO: estimate the context carried into one turn.

        Hint:
        - Include `User.md`
        - Include compact summary text
        - Include recent kept messages
        """

        context = self.compact_memory.context(thread_id)
        return estimate_tokens(self.profile_store.read_text(user_id)) + estimate_tokens(context['summary']) + sum(estimate_tokens(m['content']) for m in context['messages'])

    def _offline_response(self, user_id: str, thread_id: str, message: str) -> str:
        """Student TODO: return a deterministic answer using persisted memory.

        Make sure the advanced agent can answer questions like:
        - "Mình tên gì?"
        - "Hiện tại mình làm nghề gì?"
        - "Nhắc lại style trả lời mình thích"
        - questions in the long stress dataset
        """

        facts = self.profile_store.facts(user_id)
        # Recent user assertions can also answer temporary facts in this thread.
        for m in self.compact_memory.context(thread_id)['messages']:
            if m['role'] == 'user':
                for key, value in self.profile_policy.accepted_updates(m['content']).items():
                    facts.setdefault(key, value)
        return answer_from_facts(message, facts)

    def _maybe_build_langchain_agent(self):
        """Student TODO: wire a live agent with tools and compact middleware.

        High-level design:
        - `build_chat_model(self.config.model)` for the selected provider
        - `InMemorySaver` for short-term thread state
        - tool to read `User.md`
        - tool to write/edit `User.md`
        - dynamic prompt that injects profile memory
        - summarization middleware for long threads
        """

        if self.force_offline:
            return None
        model = self.config.model
        # No remote credentials means the scaffold's deterministic offline path.
        if model.provider != 'ollama' and not model.api_key:
            return None
        return build_chat_model(model)
