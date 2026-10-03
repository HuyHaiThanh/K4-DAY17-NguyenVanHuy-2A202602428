from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from config import LabConfig, load_config
from memory_store import estimate_tokens
from model_provider import build_chat_model

from memory_store import estimate_tokens, extract_profile_updates
from offline_response import answer_from_facts


@dataclass
class SessionState:
    messages: list[dict[str, str]] = field(default_factory=list)
    token_usage: int = 0
    prompt_tokens_processed: int = 0


class BaselineAgent:
    """Student TODO: implement Agent A.

    Requirements:
    - Within-session memory only
    - No persistent `User.md`
    - Should forget long-term facts across new threads
    """

    def __init__(self, config: LabConfig | None = None, force_offline: bool = False) -> None:
        self.config = config or load_config()
        self.force_offline = force_offline
        self.sessions: dict[str, SessionState] = {}
        self.owners = {}
        self.langchain_agent = None if force_offline else self._maybe_build_langchain_agent()

    def reply(self, user_id: str, thread_id: str, message: str) -> dict[str, Any]:
        """Student TODO: return the agent response and token accounting.

        Pseudocode:
        - If a live agent exists, call the live path.
        - Otherwise use a deterministic offline path.
        """

        if thread_id in self.owners and self.owners[thread_id] != user_id:
            raise ValueError('Thread belongs to another user')
        self.owners[thread_id] = user_id
        if self.langchain_agent is not None and not self.force_offline:
            return self._reply_live(user_id, thread_id, message)
        return self._reply_offline(thread_id, message)

    def token_usage(self, thread_id: str) -> int:
        # TODO: return cumulative agent token count for one thread.
        return self.sessions.get(thread_id, SessionState()).token_usage

    def prompt_token_usage(self, thread_id: str) -> int:
        # TODO: estimate how much prompt context this baseline kept processing.
        return self.sessions.get(thread_id, SessionState()).prompt_tokens_processed

    def compaction_count(self, thread_id: str) -> int:
        # Baseline has no compact memory.
        return 0

    def _reply_offline(self, thread_id: str, message: str) -> dict[str, Any]:
        """Student TODO: implement a simple offline behavior.

        Suggested behavior:
        - Store the new user message in the session
        - Generate a short deterministic reply
        - Update token counts
        - Never remember facts across different thread ids
        """

        state = self.sessions.setdefault(thread_id, SessionState())
        state.messages.append({'role': 'user', 'content': message})
        prompt_tokens = sum(estimate_tokens(m['content']) for m in state.messages)
        facts = {}
        for m in state.messages:
            if m['role'] == 'user':
                facts.update(extract_profile_updates(m['content']))
        answer = answer_from_facts(message, facts)
        state.messages.append({'role': 'assistant', 'content': answer})
        tokens = estimate_tokens(answer)
        state.token_usage += tokens
        state.prompt_tokens_processed += prompt_tokens
        return {'answer': answer, 'agent_tokens': tokens, 'prompt_tokens': prompt_tokens}

    def _maybe_build_langchain_agent(self):
        """Student TODO: optionally wire `create_agent` + `InMemorySaver` here.

        Use `build_chat_model(self.config.model)` so the baseline can run with any supported provider.
        """

        if self.force_offline:
            return None
        model = self.config.model
        # No remote credentials means the scaffold's deterministic offline path.
        if model.provider != 'ollama' and not model.api_key:
            return None
        from live_runtime import LiveRuntime
        return LiveRuntime(build_chat_model(model), self.config)

    def _reply_live(self, user_id: str, thread_id: str, message: str) -> dict:
        result = self.langchain_agent.reply(user_id, thread_id, message)
        state = self.sessions.setdefault(thread_id, SessionState())
        state.messages.extend([{'role': 'user', 'content': message}, {'role': 'assistant', 'content': result['answer']}])
        state.token_usage += result['agent_tokens']
        state.prompt_tokens_processed += result['prompt_tokens']
        return result
